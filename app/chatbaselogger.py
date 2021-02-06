import settings
import requests
import logging

CHATBASE_URL = 'https://chatbase-area120.appspot.com/api/message'

def sendUserMessage(message, user_id):
    try:
        request = {
            "api_key": settings.CHATBASE_API_KEY,
            "type": "user",
            "message": message,
            "platform": settings.CHATBASE_BOT_PLATFORM,
            "user_id": user_id,
            "version": settings.VERSION,
        }
        response = requests.post(
            CHATBASE_URL,
            data=None,
            json=request,
            stream=False,
            timeout=1,
        )
    except Exception as e:
        logging.error(f"CHATBASE sendBotResponse EXCEPTION:{e}" )
        return None

def sendBotResponse(message, user_id):
    try:
        request = {
            "api_key": settings.CHATBASE_API_KEY,
            "type": "agent",
            "message": message,
            "platform": settings.CHATBASE_BOT_PLATFORM,
            "user_id": user_id,
            "version": settings.VERSION,
        }
        response = requests.post(
            CHATBASE_URL,
            data=None,
            json=request,
            stream=False,
            timeout=1,
        )
    except Exception as e:
        logging.error(f"CHATBASE sendBotResponse EXCEPTION:{e}" )
        return None