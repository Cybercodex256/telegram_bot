import json
import os
import http.client
import urllib.parse

def handler(event, context):
    """Main Netlify Function handler"""
    
    # Only respond to POST requests (Telegram webhooks)
    if event.get('httpMethod') != 'POST':
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method Not Allowed'})
        }
    
    try:
        # Parse the incoming update from Telegram
        body = json.loads(event.get('body', '{}'))
        
        # Get bot token from environment variable
        BOT_TOKEN = os.environ.get('BOT_TOKEN')
        if not BOT_TOKEN:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Bot token not configured'})
            }
        
        # Process the update
        response = process_update(body, BOT_TOKEN)
        
        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

def process_update(update, bot_token):
    """Process Telegram update and send appropriate response"""
    
    # Check if update contains a message
    if 'message' not in update:
        return {'status': 'no message'}
    
    message = update['message']
    chat_id = message['chat']['id']
    text = message.get('text', '')
    username = message.get('from', {}).get('username', 'User')
    first_name = message.get('from', {}).get('first_name', 'there')
    
    # Process commands
    if text.startswith('/start'):
        response_text = f"""👋 Hello {first_name}! Welcome to my Python Telegram Bot.

🤖 Available commands:
/help - Show help message
/about - About this bot
/echo [text] - Echo your message
/python - Python-related info"""
    
    elif text.startswith('/help'):
        response_text = """📚 **Bot Help**

Commands:
• /start - Start the bot
• /help - Show this help message
• /about - About the bot
• /echo [text] - Echo back your text
• /python - Python information

Just send me a command!"""
    
    elif text.startswith('/about'):
        response_text = """ℹ️ **About This Bot**

• Built with Python 3
• Hosted on Netlify Functions
• Responds to simple commands
• Open source project"""
    
    elif text.startswith('/echo'):
        echo_text = text[6:].strip()
        if echo_text:
            response_text = f"📢 You said: {echo_text}"
        else:
            response_text = "Please add text after /echo"
    
    elif text.startswith('/python'):
        response_text = """🐍 **Python Information**

This bot is built with:
• Python 3.9+
• Netlify Functions
• Telegram Bot API

Python is awesome for bots!"""
    
    elif text:
        response_text = f"❓ I don't understand \"{text}\". Try /help for available commands."
    
    else:
        response_text = "Send me a text message or command!"
    
    # Send response to Telegram
    if response_text:
        send_telegram_message(bot_token, chat_id, response_text)
    
    return {'status': 'message processed'}

def send_telegram_message(bot_token, chat_id, text):
    """Send message to Telegram chat"""
    
    telegram_api = f"api.telegram.org"
    endpoint = f"/bot{bot_token}/sendMessage"
    
    # Prepare the request data
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    
    # Encode data
    encoded_data = urllib.parse.urlencode(data)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': str(len(encoded_data))
    }
    
    try:
        # Create HTTPS connection
        conn = http.client.HTTPSConnection(telegram_api)
        
        # Send POST request
        conn.request("POST", endpoint, encoded_data, headers)
        response = conn.getresponse()
        
        # Read response
        response_data = response.read().decode()
        conn.close()
        
        print(f"Message sent to {chat_id}: {response.status}")
        return json.loads(response_data) if response_data else {}
        
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return None
