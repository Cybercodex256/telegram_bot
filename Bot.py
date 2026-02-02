import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuration
TOKEN = "8461671654:AAFHUEZDRTC0qaj2lGoCTOl-6z7KXp6364c"
URL = "https://telegram-bot-zxg0.onrender.com"

# Initialize Flask app
app = Flask(__name__)

# Initialize Telegram Application
# We use this to handle the logic, but we won't use .run_polling()
ptb_app = Application.builder().token(TOKEN).build()

# 1. /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I'm a Python mirror bot! Send me anything.")

# 2. Mirror handler
async def mirror(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This mirrors text, stickers, photos, etc. back to the user
    await update.message.copy(chat_id=update.effective_chat.id)

# Register handlers
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(MessageHandler(filters.ALL, mirror))

# 3. The Webhook Route (Crucial for fixing the 405 error)
@app.route("/", methods=["POST"])
async def webhook():
    """Handle incoming Telegram updates."""
    if request.method == "POST":
        # Process the update
        update = Update.de_json(request.get_json(force=True), ptb_app.bot)
        await ptb_app.initialize()
        await ptb_app.process_update(update)
        return "OK", 200

@app.route("/health", methods=["GET"])
def health_check():
    """A simple GET route for Render's health checks."""
    return "Bot is alive!", 200

if __name__ == "__main__":
    # 4. Set the webhook with Telegram
    # In production, it's better to do this once, but this ensures it's set on startup
    import asyncio
    
    async def set_webhook():
        bot = Bot(TOKEN)
        await bot.set_webhook(url=URL)
    
    # Run the setup and the Flask app
    asyncio.run(set_webhook())
    
    # Render provides the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

