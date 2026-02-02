import telebot
from flask import Flask
import os

# Replace 'YOUR_TOKEN' with the API Token from BotFather
bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))

# Handles the /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I am your new bot. How can I help?")

# Echoes all incoming text messages
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)

print("Bot is running...")
bot.infinity_polling()

#SERVER TO KEEP RENDER WEBSERVICE HAPPY

try:
    app = Flask(__name__)

    @app.route('/')
    def health_check():
        return "Bot is alive!", 200

    if __name__ == "__main__":
    # Start a tiny web server in the background
        from threading import Thread
        Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))).start()
    
        # Start your bot polling
        bot.infinity_polling()
except Exception as e:
        print(f"Error: {str(e)[:50]}") 
