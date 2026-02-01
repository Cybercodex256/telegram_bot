import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# Initialize Flask and Bot
app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN")
# This will be your Render URL (e.g., https://my-bot.onrender.com)
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL") 

# Define a simple command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running as a Web Service!")

# Setup Application
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    # Process the update from Telegram
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
    return "ok", 200

@app.route("/")
def index():
    return "Bot is alive!", 200

if __name__ == "__main__":
    # Render requires binding to 0.0.0.0 and port 10000 by default
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
 
