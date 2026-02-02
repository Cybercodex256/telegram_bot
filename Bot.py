import os
from flask import Flask, request
from telegram import Bot, Update

# Configuration
TOKEN = "8461671654:AAFHUEZDRTC0qaj2lGoCTOl-6z7KXp6364c"

app = Flask(__name__)
bot = Bot(token=TOKEN)

@app.route("/", methods=["POST"])
def webhook():
    """Handles the POST request from Telegram"""
    try:
        # 1. Get the data from the request
        data = request.get_json(force=True)
        update = Update.de_json(data, bot)
        
        # 2. Extract message details
        if update.message:
            chat_id = update.message.chat_id
            text = update.message.text
            
            # 3. Logic: Handle /start or Mirror
            if text == "/start":
                bot.send_message(chat_id=chat_id, text="Python Mirror Bot is online!")
            else:
                # Mirror the message back
                update.message.copy(chat_id=chat_id)
                
        return "OK", 200
    except Exception as e:
        print(f"Error: {e}")
        return "Internal Error", 500

@app.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    # Render uses the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

