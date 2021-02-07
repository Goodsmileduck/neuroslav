import aiohttp
import asyncio
import json
import settings
import os, logging





CHATBASE_URL = 'https://chatbase-area120.appspot.com/api/message'

async def _send_message(user_id, session_id, message_type, message):
    timeout = aiohttp.ClientTimeout(total=60)
    session = aiohttp.ClientSession(timeout=timeout) 
    response = await session.post(
        CHATBASE_URL,
        data=json.dumps(
            {
                "api_key": settings.CHATBASE_API_KEY,
                "type": message_type,
                "message": message,
                "platform": settings.CHATBASE_BOT_PLATFORM,
                "user_id": user_id,
                "session_id": session_id,
                "version": settings.VERSION
#                "intent": intent
#                "not_handled": not_handled
            }
        ),
    )
    if response.status != 200:
        logger.info("error submiting stats %d", response.status)
    await response.release()

async def sendUserMessage(message, user_id, session_id):
    try:
        if message == '':
            message = '<empty>'
        message_type = 'user'
        logging.debug(f'CHATBASE user message: [{message}] Session_id: {session_id}')
        asyncio.ensure_future(_send_message(user_id, session_id, message_type, message))
    except Exception as e:
        logging.error(f"CHATBASE sendBotResponse EXCEPTION:{e}" )
        return None

async def sendBotResponse(message, user_id, session_id):
    try:
        if message == '':
            message = '<empty>'
        message_type = 'agent'
        logging.info(f'CHATBASE bot response: [{message}] Session_id: {session_id}')
        asyncio.ensure_future(_send_message(user_id, session_id, message_type, message))
    except Exception as e:
        logging.error(f"CHATBASE sendBotResponse EXCEPTION:{e}" )
        return None