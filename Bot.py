import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import requests
import yt_dlp
from flask import Flask
import threading
from static_ffmpeg import add_paths

add_paths()

# --- CONFIGURATION ---
BOT_TOKEN = "8461671654:AAFHUEZDRTC0qaj2lGoCTOl-6z7KXp6364c"
STORAGE_CHANNEL_ID = "-1003931494429"
PROXY_URL = 'http://opfxmeil:dqti3mkecvnk@31.59.20.176:6754/'

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

movie_cache = {}
user_links = {}

@app.route('/')
def health_check(): return "Bot is alive!", 200

# --- RELIABLE INTERNET ARCHIVE API SEARCH ---
@bot.message_handler(commands=['movie'])
def search_movie_options(message):
    query = message.text.replace('/movie', '').strip()
    if not query:
        bot.reply_to(message, "Usage: /movie [name]")
        return

    status = bot.reply_to(message, f"🔍 Searching Archive.org for '{query}'...")

    # Using the official Search API instead of scraping
    search_api = (
        f"https://archive.org/advancedsearch.php?q={query.replace(' ', '+')}+AND+mediatype:movies"
        f"&fl[]=identifier&fl[]=title&sort[]=downloads+desc&rows=5&output=json"
    )

    try:
        response = requests.get(search_api, proxies={"http": PROXY_URL, "https": PROXY_URL}).json()
        docs = response.get('response', {}).get('docs', [])

        if not docs:
            bot.edit_message_text("❌ No movies found on Archive.org.", message.chat.id, status.message_id)
            return

        markup = InlineKeyboardMarkup()
        for i, doc in enumerate(docs):
            title = doc.get('title', 'Unknown Title')
            identifier = doc.get('identifier')
            url = f"https://archive.org/details/{identifier}"
            
            movie_cache[str(i)] = {"title": title, "url": url}
            markup.add(InlineKeyboardButton(f"🎬 {title[:45]}", callback_data=f"ia_{i}"))

        bot.edit_message_text(f"Select a version for '{query}':", message.chat.id, status.message_id, reply_markup=markup)

    except Exception as e:
        bot.edit_message_text(f"❌ API Error: {str(e)}", message.chat.id, status.message_id)

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
    is_movie = call.data.startswith("ia_")
    target_url = ""
    
    if is_movie:
        idx = call.data.replace("ia_", "")
        movie_info = movie_cache.get(idx)
        if not movie_info:
            bot.answer_callback_query(call.id, "Error: Search expired.")
            return
        target_url = movie_info['url']
    else:
        target_url = user_links.get(call.message.chat.id)

    if not target_url:
        bot.answer_callback_query(call.id, "Error: Link lost.")
        return

    status = bot.send_message(call.message.chat.id, "⏳ Downloading and Cloud Saving...")

    ydl_opts = {
        'proxy': PROXY_URL,
        'format': 'best',
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True
    }

    if not is_movie and call.data == "audio_mp3":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=True)
            filename = ydl.prepare_filename(info)
            if not is_movie and call.data == "audio_mp3":
                filename = os.path.splitext(filename)[0] + ".mp3"

        with open(filename, 'rb') as f:
            if not is_movie and call.data == "audio_mp3":
                stored_msg = bot.send_audio(STORAGE_CHANNEL_ID, f, caption=f"File: {info.get('title')}")
                if stored_msg: bot.send_audio(call.message.chat.id, stored_msg.audio.file_id)
            else:
                stored_msg = bot.send_video(STORAGE_CHANNEL_ID, f, caption=f"File: {info.get('title')}")
                if stored_msg: bot.send_video(call.message.chat.id, stored_msg.video.file_id)
        
        os.remove(filename)
        bot.delete_message(call.message.chat.id, status.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Download Error: {str(e)}", call.message.chat.id, status.message_id)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()

