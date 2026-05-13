import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
import yt_dlp
from flask import Flask
import threading
from static_ffmpeg import add_paths

add_paths()

# --- CONFIGURATION ---
BOT_TOKEN = "8461671654:AAFHUEZDRTC0qaj2lGoCTOl-6z7KXp6364c"
STORAGE_CHANNEL_ID = "-1003931494429"
OMDB_API_KEY = "43a3c1dc" 
PROXY_URL = 'http://opfxmeil:dqti3mkecvnk@31.59.20.176:6754/'

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

movie_cache = {}
user_links = {}

@app.route('/')
def health_check(): return "Bot is alive!", 200

# --- FIXED MOVIE SEARCH LOGIC ---
@bot.message_handler(commands=['movie'])
def search_movie_options(message):
    query = message.text.replace('/movie', '').strip()
    if not query:
        bot.reply_to(message, "Usage: /movie [name]")
        return

    # 1. Try general search ('s=') for a list of options
    url = f"http://www.omdbapi.com/?s={query}&apikey={OMDB_API_KEY}"
    try:
        response = requests.get(url).json()
        markup = InlineKeyboardMarkup()

        if response.get('Response') == 'True':
            for movie in response.get('Search', [])[:5]:
                title, year, imdb_id = movie['Title'], movie['Year'], movie['imdbID']
                movie_cache[imdb_id] = f"{title} {year}"
                markup.add(InlineKeyboardButton(f"🎬 {title} ({year})", callback_data=f"select_{imdb_id}"))
            bot.send_message(message.chat.id, f"Select version for '{query}':", reply_markup=markup)
        
        else:
            # 2. FALLBACK: Try direct title search ('t=') if general search fails
            fallback_url = f"http://www.omdbapi.com/?t={query}&apikey={OMDB_API_KEY}"
            fb_res = requests.get(fallback_url).json()
            
            if fb_res.get('Response') == 'True':
                title, year, imdb_id = fb_res['Title'], fb_res['Year'], fb_res['imdbID']
                movie_cache[imdb_id] = f"{title} {year}"
                markup.add(InlineKeyboardButton(f"🎬 {title} ({year})", callback_data=f"select_{imdb_id}"))
                bot.send_message(message.chat.id, f"Found exact match for '{query}':", reply_markup=markup)
            else:
                bot.reply_to(message, "❌ No movies found. Try a shorter name.")
    except Exception as e:
        bot.reply_to(message, f"Search Error: {str(e)}")

@bot.message_handler(func=lambda m: 'youtube.com' in m.text or 'youtu.be' in m.text)
def handle_youtube_link(message):
    user_links[message.chat.id] = message.text
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Video (720p)", callback_data="vid_720"),
               InlineKeyboardButton("Video (360p)", callback_data="vid_360"),
               InlineKeyboardButton("Audio (MP3)", callback_data="audio_mp3"))
    bot.send_message(message.chat.id, "Select format:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    is_movie = call.data.startswith("select_")
    target_url = ""
    
    if is_movie:
        imdb_id = call.data.replace("select_", "")
        movie_name = movie_cache.get(imdb_id)
        # FIXED: Improved Archive search URL by using the cleaned OMDb title
        target_url = f"https://archive.org/details/{movie_name.replace(' ', '+')}"
    else:
        target_url = user_links.get(call.message.chat.id)

    if not target_url:
        bot.answer_callback_query(call.id, "Error: Data lost.")
        return

    status = bot.send_message(call.message.chat.id, "⏳ Downloading and Cloud Saving...")

    if not is_movie and call.data == "audio_mp3":
        ydl_opts = {
            'proxy': PROXY_URL,
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'outtmpl': '%(title)s.%(ext)s', 'quiet': True
        }
    elif is_movie:
        ydl_opts = {
            'proxy': PROXY_URL,
            'format': 'best',
            'outtmpl': '%(title)s.%(ext)s', 'quiet': True
        }
    else:
        res = "720" if "720" in call.data else "360"
        ydl_opts = {
            'proxy': PROXY_URL,
            'format': f'bestvideo[height<={res}][ext=mp4]+bestaudio[ext=m4a]/best',
            'outtmpl': '%(title)s.%(ext)s', 'quiet': True
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=True)
            filename = ydl.prepare_filename(info)
            if not is_movie and call.data == "audio_mp3":
                filename = os.path.splitext(filename)[0] + ".mp3"

        # --- STORAGE CHANNEL UPLOAD ---
        with open(filename, 'rb') as f:
            if not is_movie and call.data == "audio_mp3":
                stored_msg = bot.send_audio(STORAGE_CHANNEL_ID, f, caption=f"File: {info.get('title')}")
                if stored_msg and hasattr(stored_msg, 'audio'):
                    bot.send_audio(call.message.chat.id, stored_msg.audio.file_id)
                else:
                    bot.send_message(call.message.chat.id, "❌ Error: Storage upload failed.")
            else:
                stored_msg = bot.send_video(STORAGE_CHANNEL_ID, f, caption=f"File: {info.get('title')}")
                if stored_msg and hasattr(stored_msg, 'video'):
                    bot.send_video(call.message.chat.id, stored_msg.video.file_id)
                else:
                    bot.send_message(call.message.chat.id, "❌ Error: Storage upload failed.")
        
        os.remove(filename)
        bot.delete_message(call.message.chat.id, status.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", call.message.chat.id, status.message_id)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()

