import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading
import os
import yt_dlp
from static_ffmpeg import add_paths

# Ensure ffmpeg paths are added for audio conversion
add_paths()

# 1. Setup Flask
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is alive!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. Setup Bot
bot = telebot.TeleBot("8461671654:AAFHUEZDRTC0qaj2lGoCTOl-6z7KXp6364c")

# ADD YOUR CHANNEL ID HERE (Use the -100 prefix)
STORAGE_CHANNEL_ID = "-1003931494429" 

# Dictionary to store URLs temporarily
user_links = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I am your new bot. How can I help?")

@bot.message_handler(func=lambda m: 'youtube.com' in m.text or 'youtu.be' in m.text)
def handle_video(message):
    # Store URL for the callback handler
    user_links[message.chat.id] = message.text
    
    # Create the Menu
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("Video (720p)", callback_data="vid_720"),
        InlineKeyboardButton("Video (360p)", callback_data="vid_360"),
        InlineKeyboardButton("Audio (MP3)", callback_data="audio_mp3")
    )
    bot.send_message(message.chat.id, "Select format and quality:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    url = user_links.get(call.message.chat.id)
    if not url:
        bot.answer_callback_query(call.id, "Error: Resend the link.")
        return

    bot.answer_callback_query(call.id, "Starting download...")
    status = bot.send_message(call.message.chat.id, "⏳ Processing and Cloud Saving...")

    # Your strict proxy and download settings
    proxy_url = 'http://opfxmeil:dqti3mkecvnk@31.59.20.176:6754/'
    
    if call.data == "audio_mp3":
        ydl_opts = {
            'proxy': proxy_url,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True
        }
        mode = 'audio'
    else:
        res = "720" if "720" in call.data else "360"
        ydl_opts = {
            'proxy': proxy_url,
            'format': f'bestvideo[height<={res}][ext=mp4]+bestaudio[ext=m4a]/best[height<={res}][ext=mp4]/best',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True
        }
        mode = 'video'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if mode == 'audio':
                filename = os.path.splitext(filename)[0] + ".mp3"

        # Upload to channel first, then send file_id to user
        with open(filename, 'rb') as f:
            if mode == 'video':
                # Upload to storage channel
                stored_msg = bot.send_video(STORAGE_CHANNEL_ID, f, caption=f"Stored: {info.get('title')}")
                # Send to user via file_id
                bot.send_video(call.message.chat.id, stored_msg.video.file_id, caption=info.get('title'))
            else:
                # Upload to storage channel
                stored_msg = bot.send_audio(STORAGE_CHANNEL_ID, f, caption=f"Stored: {info.get('title')}")
                # Send to user via file_id
                bot.send_audio(call.message.chat.id, stored_msg.audio.file_id, caption=info.get('title'))
        
        os.remove(filename)
        bot.delete_message(call.message.chat.id, status.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", call.message.chat.id, status.message_id)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)

# 3. Start both
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Webserver started, bot is now polling...")
    bot.infinity_polling()

