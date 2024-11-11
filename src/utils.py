import requests
import os
from dotenv import load_dotenv


def discord_webhook_log(message, username):
    load_dotenv()
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    data = {
        "content": message,
        "username": username
    }
    
    requests.post(webhook_url, json=data)