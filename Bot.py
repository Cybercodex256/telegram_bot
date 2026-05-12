import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading
import os
import yt_dlp
from static_ffmpeg import add_paths

# Ensure ffmpeg paths are added for audio conversion
add_paths()

# 1. Setup Flask (Keeps the bot alive on Render)
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is alive!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. Setup Bot
# Using the token you provided
BOT_TOKEN = "8461671654:AAFHUEZDRTC0qaj2lGoCTOl-6z7KXp6364c"
bot = telebot.TeleBot(BOT_TOKEN)

# Store URL in memory to link it to the button click
user_links = {}
PROXY_URL = 'http://opfxmeil:dqti3mkecvnk@31.59.20.176:6754/'

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello Edwin! Send me a YouTube link to start.")

@bot.message_handler(func=lambda m: 'youtube.com' in m.text or 'youtu.be' in m.text)
def handle_link(message):
    user_links[message.chat.id] = message.text
    
    # The Menu
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("Video (720p)", callback_data="vid_720"),
        InlineKeyboardButton("Video (360p)", callback_data="vid_360"),
        InlineKeyboardButton("Audio (MP3)", callback_data="audio_mp3")
    )
    bot.send_message(message.chat.id, "Select format and quality:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    url = user_links.get(call.message.chat.id)
    if not url:
        bot.answer_callback_query(call.id, "Error: Link not found. Please resend the link.")
        return

    bot.answer_callback_query(call.id, "Starting download...")
    status = bot.send_message(call.message.chat.id, "⏳ Processing...")

    # Configuration for yt-dlp
    if call.data == "audio_mp3":
        ydl_opts = {
            'proxy': PROXY_URL,
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
            'proxy': PROXY_URL,
            'format': f'bestvideo[height<={res}][ext=mp4]+bestaudio[ext=m4a]/best[height<={res}][ext=mp4]/best',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True
        }
        mode = 'video'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Adjust filename if converted to mp3
            if mode == 'audio':
                filename = os.path.splitext(filename)[0] + ".mp3"

        # Sending the file
        with open(filename, 'rb') as f:
            if mode == 'video':
                bot.send_video(call.message.chat.id, f, caption=info.get('title'))
            else:
                bot.send_audio(call.message.chat.id, f, caption=info.get('title'))
        
        # Cleanup: Delete the file after sending to save space
        os.remove(filename)
        bot.delete_message(call.message.chat.id, status.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", call.message.chat.id, status.message_id)

# 3. Execution
if __name__ == "__main__":
    # Run Flask in background thread
    threading.Thread(target=run_flask).start()
    print("Webserver and Bot are running...")
    # Polling blocks the main thread
    bot.infinity_polling()

