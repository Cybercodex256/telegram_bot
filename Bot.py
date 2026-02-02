from os import environ
import telebot

# Replace 'YOUR_TOKEN' with the API Token from BotFather
bot = telebot.TeleBot(environ.get('BOT_TOKEN'))
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


