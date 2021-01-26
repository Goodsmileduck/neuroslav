import logging, json
from flask import Flask, request
from state import STATE_REQUEST_KEY
from scenes import SCENES, DEFAULT_SCENE
from request import Request

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

@app.route("/", methods=['POST'])
def main():
# Функция получает тело запроса и возвращает ответ.
    logging.info('Request: %r', request.json)


    response = handler(request.json)

    logging.info('Response: %r', response)

    return json.dumps(
        response,
        ensure_ascii=False,
        indent=2
    )



def handler(request):

    logging.debug(request)
    current_scene_id = request.get('state', {}).get(STATE_REQUEST_KEY, {}).get('scene')
    print(current_scene_id)
    if current_scene_id is None:
        return DEFAULT_SCENE().reply(request)
    current_scene = SCENES.get(current_scene_id, DEFAULT_SCENE)()
    next_scene = current_scene.move(request)
    if next_scene is not None:
        logging.info(f'Moving from scene {current_scene.id()} to {next_scene.id()}')
        return next_scene.reply(request)
    else:
        logging.warn(f'Failed to parse user request at scene {current_scene.id()}')
        return current_scene.fallback(request)

if __name__ == '__main__':
    app.run()