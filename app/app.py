import logging, json
from flask import Flask, request
from state import STATE_REQUEST_KEY, STATE_RESPONSE_KEY
from scenes import SCENES, DEFAULT_SCENE
from request import Request
import seeder
import debug

import chatbaselogger
import settings

app = Flask(__name__)

logging.basicConfig(
    format=u'[%(asctime)s] %(levelname)-8s  %(message)s',
    level=logging.DEBUG)


@app.route("/", methods=['POST'])
def main():
    # Функция получает тело запроса и возвращает ответ.
    request_obj = request.json
    session_id = request_obj.get('session', {}).get('session_id', None)
    
    logging.info(f'Session_id: {session_id} Request: {request_obj}')

    user_id = request_obj['session'].get('application').get('application_id')
    if settings.SEND_TO_CHATBASE:
        user_message = request_obj['request']['command']
        #logging.info(f'User message: [{user_message}]')
        chatbaselogger.sendUserMessage(user_id=user_id, message=user_message)

    response = handler(request_obj)

    logging.info(f'Session_id: {session_id} Response: {response}')

    if settings.SEND_TO_CHATBASE:
        response_message = response['response']['text']
        #logging.info(f'Response message: [{response_message}]')
        chatbaselogger.sendBotResponse(user_id=user_id, message=response_message)

    return json.dumps(
        response,
        ensure_ascii=False,
        indent=2
    )


def handler(request):
    if 'state' in request:
      current_scene_id = request.get('state', {}).get(STATE_REQUEST_KEY, {}).get('scene', None)
    else:
      current_scene_id = None
    logging.info('CURRENT SCENE ID: %r', current_scene_id)
    request_obj = Request(request)

    if current_scene_id is None:
        return DEFAULT_SCENE().reply(request_obj)
    current_scene = SCENES.get(current_scene_id, DEFAULT_SCENE)()
    next_scene = current_scene.move(request_obj)
    if next_scene is not None:
        logging.info(f'Moving from scene {current_scene.id()} to {next_scene.id()}')
        return next_scene.reply(request_obj)
    else:
        logging.warning(f'Failed to parse user request at scene {current_scene.id()}')
        return current_scene.fallback(request_obj)


if __name__ == '__main__':
    seeder.seed_all()
    debug.test()
    app.run(host='0.0.0.0')


