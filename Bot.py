import telebot
from flask import Flask
import threading
import os
import yt_dlp
from static_ffmpeg import add_paths

# 1. Setup Flask
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is alive!", 200

def run_flask():
    # Render usually uses port 10000 or the PORT env variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. Setup Bot
bot = telebot.TeleBot("8461671654:AAFHUEZDRTC0qaj2lGoCTOl-6z7KXp6364c") # Use your full token

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I am your new bot. How can I help?")

@bot.message_handler(func=lambda m: 'youtube.com' in m.text or 'youtu.be' in m.text)
def handle_video(message):
    status = bot.reply_to(message, "⏳ Processing... this may take a minute.")
    
    # We use 'bestvideo[filesize<50M]+bestaudio/best[filesize<50M]' 
    # to try and stay under the Telegram limit.
    ydl_opts = {
        'cookiefile':'cookies.txt',
        'format': 'best[ext=mp4][filesize<50M]/best[filesize<50M]',
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(message.text, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as f:
            bot.send_video(message.chat.id, f, caption=info.get('title'))
        
        os.remove(filename) # Clean up Render's limited disk space
        bot.delete_message(message.chat.id, status.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, status.message_id)




@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)

# 3. Start both
if __name__ == "__main__":
    # Start Flask in a background thread
    threading.Thread(target=run_flask).start()
    
    print("Webserver started, bot is now polling...")
    # Start the bot (this blocks the main thread)
    bot.infinity_polling()

