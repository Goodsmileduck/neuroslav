#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, logging
import csv
from random import shuffle, choice
from aiohttp import web
from aioalice import Dispatcher, get_new_configured_app, types
from aioalice.types import Entity, EntityType
from aioalice.dispatcher import MemoryStorage, SkipHandler
from aioalice.utils.helper import Helper, HelperMode, Item
from settings import *
#from chatbase import track_message, track_click
#from database import db
from aiohttp_healthcheck import HealthCheck

DIALOG_ID = '2514ff74-bc13-4ed1-9843-72606bba9909'
DIALOG_URL = "https://dialogs.yandex.ru/store/skills/0bdc015e-skazki-ot-kejsi"


REVIEW_BUTTON = {
    "title": "Поставить оценку в каталоге",
    "payload": "review",
    "url": DIALOG_URL,
    "hide": False
}



LOG_LEVEL_DICT = {"DEBUG": logging.DEBUG,
                  "INFO": logging.INFO,
                  "WARNING": logging.WARNING}


class States(Helper):
    mode = HelperMode.snake_case

    NAME = Item()

logging.basicConfig(
    format=u'[%(asctime)s] %(levelname)-8s  %(message)s',
    level=LOG_LEVEL_DICT[LOG_LEVEL])

# Создаем экземпляр диспетчера и подключаем хранилище в памяти
dp = Dispatcher(storage=MemoryStorage())

#choose_buttons = ["Еще сказку", "Повтори", "Перевод", "Я не слышу", "Хватит"]

names_list = ['Джеймс Бонд', 'Чебурашка', 'Громозека', 'Винни', 'Пяточёк']


@dp.request_handler()
async def take_all_requests(alice_request):
    # Логгируем запрос. Можно записывать в БД и тд
    logging.debug('New request! %r', alice_request)
    # Поднимаем исключение, по которому обработка перейдёт
    # к следующему хэндлеру, у которого подойдут фильтры
    raise SkipHandler

@dp.request_handler(commands='ping')
async def send_pong(alice_request):
    user_id = alice_request.session.user_id
    logging.info(f"Ping from {user_id}")
    return alice_request.response('pong')

# Новая сессия. Приветствуем пользователя
#@dp.request_handler(func=lambda areq: areq.session.new)
@dp.request_handler(func=lambda areq: areq.session.new)
async def handle_new_session(alice_request):
    user_id = alice_request.session.user_id
    session_id = alice_request.session.session_id
    logging.info(f'Initialized new session! user_id is {user_id!r}')
    return alice_request.response(
        f"Привет, скажи число от 1 до 9")


@dp.request_handler(commands='дота')
async def handle_dota(alice_request):
    user_id = alice_request.session.user_id
    session_id = alice_request.session.session_id
    logging.info(f'Initialized new session! user_id is {user_id!r}')
    #exist = db.users.find_one({'_id': user_id})
    hero = db.heroes.find_one({'hero': 'crystal-maiden'})
    worstvs = hero['wvs'][:4]
    worstvs_rus = []
    for item in worstvs:
        worstvs_rus.append(heroes[item])
    worstvs_str = ", ".join(worstvs_rus)
    hero_name = heroes['crystal-maiden']
    return alice_request.response(
        f"Привет! Вот какими героями на этой неделе контрят {hero_name} - \n"
        f"{worstvs_str}\n"
        f"Хорошей игры!")

URL_BUTTON1 = {
    "title": "Button with url and payload.",
    "payload": "button1",
    "url": "http://ya.ru",
    "hide": False
}

URL_BUTTON2 = {
    "title": "Suggest with url and payload.",
    "payload": "button2",
    "url": "http://ya.ru",
    "hide": True
}

URL_BUTTON4 = {
    "title": "Suggest with url.",
    "url": "http://ya.ru",
    "hide": True
}

URL_BUTTON3 = {
    "title": "Button with url.",
    "url": "http://ya.ru",
    "hide": False
}

URL_BUTTON6 = {
    "title": "Suggest with payload.",
    "payload": "button5",
    "hide": True
}

URL_BUTTON5 = {
    "title": "Button with payload.",
    "payload": "button6",
    "hide": False
}

@dp.request_handler(commands='1')
async def handle_1(alice_request):
    return alice_request.response(
        f"Example text for button with url and payload.\n"
        f"Here how it should looks like",
        buttons=[URL_BUTTON1])

@dp.request_handler(commands='2')
async def handle_2(alice_request):
    return alice_request.response(
        f"Example text for suggest with url and payload.\n"
        f"Here how it should looks like",
        buttons=[URL_BUTTON2])

@dp.request_handler(commands='3')
async def handle_3(alice_request):
    return alice_request.response(
        f"Example text for button with url.\n"
        f"Here how it should looks like",
        buttons=[URL_BUTTON3])

@dp.request_handler(commands='4')
async def handle_4(alice_request):
    return alice_request.response(
        f"Example text for suggest with url.\n"
        f"Here how it should looks like",
        buttons=[URL_BUTTON4])

@dp.request_handler(commands='5')
async def handle_5(alice_request):
    return alice_request.response(
        f"Example text for button with payload.\n"
        f"Here how it should looks like",
        buttons=[URL_BUTTON5])

@dp.request_handler(commands='6')
async def handle_6(alice_request):
    return alice_request.response(
        f"Example text for suggest with payload.\n"
        f"Here how it should looks like",
        buttons=[URL_BUTTON6])

BUTTONS1 = {
    "image_id": '1030494/e342fbf54fbcb28b56a1',
    "title": "Title",
    "description": "description",
    "button": {
        "text": "Image button",
        "url": "https://example.com/",
        "payload": "button7"
    }

}
FOOTER1 = {
    "text": "Text in footer",
    "button": {
        "text": "Button in footer",
        "url": "https://example.com/",
        "payload": "footer"
    }
}

@dp.request_handler(commands='7')
async def handle_7(alice_request):
    return alice_request.response_items_list(
            'Example reply for skill',
            'Header for List of images',
            [BUTTONS1, BUTTONS1],
            footer=FOOTER1)

@dp.request_handler(commands='8')
async def handle_8(alice_request):
    return alice_request.response_items_list(
            'Example reply for skill',
            'Header for List of images',
            [BUTTONS1, BUTTONS1],
            footer=FOOTER1,
            buttons=[URL_BUTTON2])

CARD_BUTTON = {
        "text": "Button in card",
        "url": "https://example.com/",
        "payload": "card_button"
}


@dp.request_handler(commands='9')
async def handle_9(alice_request):
    return alice_request.response_big_image(
            'Example reply for skill',
            '1030494/e342fbf54fbcb28b56a1',
            'Card title',
            'Card description',
            button=CARD_BUTTON,
            buttons=[URL_BUTTON2])


@dp.request_handler(commands='10')
async def handle_10(alice_request):
    return alice_request.response_big_image(
            'Example reply for skill',
            '1030494/e342fbf54fbcb28b56a1',
            'Card title',
            'Card description',
            button=CARD_BUTTON,
            buttons=[URL_BUTTON1])


if __name__ == '__main__':
    health = HealthCheck()
    #DEFAULT_ERROR_RESPONSE_TEXT = "Произошла непредвиденная ошибка, отправьте разработчику телеграмму немедля."
    app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_URL_PATH)
    app.router.add_get("/healthz", health)
    #app.router.add_get("/metrics", aio.web.server_stats)
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
