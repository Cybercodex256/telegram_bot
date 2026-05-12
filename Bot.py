import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading
import os
import yt_dlp

# 1. Setup Flask for Render/Hosting
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is alive!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. Setup Bot
# Replace with your actual bot token
BOT_TOKEN = "8461671654:AAFHUEZDRTC0qaj2lGoCTOl-6z7KXp6364c"
bot = telebot.TeleBot(BOT_TOKEN)

# Temporary storage for user URLs
user_links = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "YouTube Downloader Active. Send me a link to begin!")

@bot.message_handler(func=lambda m: 'youtube.com' in m.text or 'youtu.be' in m.text)
def show_menu(message):
    # Store the URL to use after the user clicks a button
    user_links[message.chat.id] = message.text
    
    # Create the quality and format menu
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("Video - 720p", callback_data="vid_720"),
        InlineKeyboardButton("Video - 360p", callback_data="vid_360"),
        InlineKeyboardButton("Audio - MP3", callback_data="audio_mp3")
    )
    bot.send_message(message.chat.id, "Select your preferred format:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_selection(call):
    url = user_links.get(call.message.chat.id)
    if not url:
        bot.answer_callback_query(call.id, "Link expired. Please send the link again.")
        return

    bot.answer_callback_query(call.id, "Starting download...")
    status = bot.send_message(call.message.chat.id, "⏳ Downloading and processing...")

    # Your specific proxy
    proxy_url = 'http://opfxmeil:dqti3mkecvnk@31.59.20.176:6754/'

    # Configure yt-dlp based on button choice
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
            
            # If audio, yt-dlp changes the extension to .mp3 after post-processing
            if mode == 'audio':
                filename = os.path.splitext(filename)[0] + ".mp3"

        # Send the file to the user
        with open(filename, 'rb') as f:
            if mode == 'video':
                bot.send_video(call.message.chat.id, f, caption=info.get('title'))
            else:
                bot.send_audio(call.message.chat.id, f, caption=info.get('title'))
        
        # Immediate cleanup for storage management
        os.remove(filename)
        bot.delete_message(call.message.chat.id, status.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", call.message.chat.id, status.message_id)

# 3. Start Both Services
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Bot is polling...")
    bot.infinity_polling()

