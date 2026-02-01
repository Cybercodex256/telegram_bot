import os
import asyncio
from flask import Flask, request
from telegram import Bot, Update

app = Flask(__name__)

# Replace with your actual token or use an environment variable
TOKEN = "8461671654:AAFHUEZDRTC0qaj2lGoCTOl-6z7KXp6364c"
bot = Bot(token=TOKEN)

@app.route("/", methods=["POST"])
async def webhook():
    if request.method == "POST":
        try:
            # 1. Parse the update from Telegram
            data = await request.get_json(force=True)
            update = Update.de_json(data, bot)

            if update.message:
                chat_id = update.message.chat_id
                text = update.message.text

                # 2. Handle /start command
                if text == "/start":
                    await bot.send_message(chat_id=chat_id, text="Hello! I am your bot. I am now working correctly.")
                
                # 3. Handle other text (Echo)
                else:
                    # Using copy to repeat what the user sent
                    await update.message.copy(chat_id=chat_id)

            return "OK", 200
        
        except Exception as e:
            print(f"Error processing update: {e}")
            return "Error", 500
    
    return "Method Not Allowed", 405

if __name__ == "__main__":
    # Render provides the PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

