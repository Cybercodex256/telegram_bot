import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Configuration
TOKEN = "8461671654:AAFHUEZDRTC0qaj2lGoCTOl-6z7KXp6364c"
URL = "https://telegram-bot-zxg0.onrender.com"

app = Flask(__name__)

# Initialize Application without starting it globally
ptb_app = Application.builder().token(TOKEN).build()

async def start(update: Update, context):
    await update.message.reply_text("Mirror bot is active!")

async def mirror(update: Update, context):
    if update.message:
        await update.message.copy(chat_id=update.effective_chat.id)

# Setup handlers
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(MessageHandler(filters.ALL, mirror))

@app.route("/", methods=["POST"])
async def webhook():
    """This handles the incoming POST from Telegram"""
    try:
        # Use the global ptb_app to process the update
        async with ptb_app:
            update = Update.de_json(request.get_json(force=True), ptb_app.bot)
            await ptb_app.process_update(update)
        return "OK", 200
    except Exception as e:
        print(f"Error processing update: {e}")
        return "Internal Error", 500

@app.route("/set_webhook", methods=["GET"])
async def register_webhook():
    """Visit this URL once in your browser to link the bot to Render"""
    async with ptb_app:
        success = await ptb_app.bot.set_webhook(url=URL)
    return f"Webhook setup: {success}", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Note: In production on Render, use a proper ASGI server or Flask's async mode
    app.run(host="0.0.0.0", port=port)

