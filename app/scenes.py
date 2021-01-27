import enum
import inspect
import sys
from abc import ABC, abstractmethod
from typing import Optional

import intents
from request import Request
from response_helpers import (
    GEOLOCATION_ALLOWED,
    GEOLOCATION_REJECTED,
    button,
    has_location,
    image_gallery,
)
from state import STATE_RESPONSE_KEY, STATE_REQUEST_KEY


class Scene(ABC):

    @classmethod
    def id(self):
        return self.__name__

    """Генерация ответа сцены"""
    @abstractmethod
    def reply(self, request):
        raise NotImplementedError()

    """Проверка перехода к новой сцене"""
    def move(self, request: Request):
        next_scene = self.handle_local_intents(request)
        if next_scene is None:
            next_scene = self.handle_global_intents(request)
        return next_scene

    @abstractmethod
    def handle_global_intents(self, request):
        raise NotImplementedError()

    @abstractmethod
    def handle_local_intents(self, request: Request) -> Optional[str]:
        raise NotImplementedError()

    def fallback(self, request: Request):
        return self.make_response('Извините, я вас не поняла. Пожалуйста, попробуйте переформулировать вопрос.')

    def make_response(self, text, tts=None, card=None, state=None, buttons=None, directives=None):
        response = {
            'text': text,
            'tts': tts if tts is not None else text,
        }
        if card is not None:
            response['card'] = card
        if buttons is not None:
            response['buttons'] = buttons
        if directives is not None:
            response['directives'] = directives
        webhook_response = {
            'response': response,
            'version': '1.0',
            STATE_RESPONSE_KEY: {
                'scene': self.id(),
            },
        }
        if state is not None:
            webhook_response[STATE_RESPONSE_KEY].update(state)
        return webhook_response


class Main(Scene):
    def handle_global_intents(self, request):
        if intents.START_QUIZ in request.get('request', {}).get('intents', {}):
            return StartQuiz()


class Welcome(Main):
    def reply(self, request: Request):
        text = 'Здравствуй! Я нейросеть-экскурсовод по Великому Новгороду. Но, честно говоря, ' \
               'после пожара в царской серверной я мало что помню.. ' \
               'Кажется, меня зовут Нейрослав. Можешь помочь мне восстановить некоторые факты?'
        response = self.make_response(text, buttons=[
            button('Давай играть', hide=True)])
        return response

    def handle_local_intents(self, request: Request):
        if request.get('request', {}).get('command', None) == 'давай играть':
            return StartQuiz()


class StartQuiz(Main):
    def reply(self, request: Request):
        text = 'Мы начинаем викторину!'
        return self.make_response(text, buttons=[
            button('Да'),
            button('Нет'),
        ])

    def handle_local_intents(self, request: Request):
        if request.get('request', {}).get('command', None) == 'да':
            return AskQuestion()


class AskQuestion(Main):
    def reply(self, request: Request):
        # Asking random question
        text = 'Да или нет?'
        return self.make_response(text, state={
            'question_id': 999,
        }, buttons=[
            button('Да'),
            button('Нет'),
            button('Подсказка'),
            button('Пропустить'),
        ])

    def clue(self, request: Request):
        text = 'Сделал вид, что подсказал'
        return self.make_response(text, state={
            'question_id': 999,
            'clue': True
        })

    def handle_local_intents(self, request: Request):
        # Check if response contains right answer
        if request.get('request', {}).get('command', None) == 'да':
            return RightAnswer()

        # Handle local intents (skip question, clue)
        if request.get('request', {}).get('command', None) == 'подсказка':
            self.clue(request)
        elif request.get('request', {}).get('command', None) == 'пропустить':
            return SkipQuestion()

        # Assume answer as wrong
        if request.get('request', {}).get('command', None) == 'нет':
            return WrongAnswer()


class SkipQuestion(Main):
    def reply(self, request: Request):
        if request.get('state', {}).get(STATE_REQUEST_KEY, {}).get('clue'):
            # The clue has already given
            return AskQuestion()
        text = 'Дать подсказку?'
        return self.make_response(text, buttons=[
            button('Да'),
            button('нет'),
        ])

    def handle_local_intents(self, request: Request):
        if request.get('request', {}).get('command', None) == 'да':
            return AskQuestion.clue()
        elif request.get('request', {}).get('command', None) == 'нет':
            return AskQuestion()


class RightAnswer(Main):
    def reply(self, request: Request):
        text = 'Верно!'
        return self.make_response(text, buttons=[
            button('Дальше'),
        ])

    def handle_local_intents(self, request: Request):
        if request.get('request', {}).get('command', None) == 'дальше':
            return AskQuestion()


class WrongAnswer(Main):
    def reply(self, request: Request):
        text = 'Не угадал, попробуешь ещё раз?'
        return self.make_response(text, buttons=[
            button('Да'),
            button('Нет'),
            button('Подскажи'),
        ])

    def handle_local_intents(self, request: Request):
        if request.get('request', {}).get('command', None) == 'да':
            return AskQuestion()
        elif request.get('request', {}).get('command', None) == 'нет':
            return Goodbye()
        elif request.get('request', {}).get('command', None) == 'подскажи':
            return AskQuestion.clue()


class Goodbye(Main):
    def reply(self, request: Request):
        text = 'Буду рад видеть тебя снова!'
        response = self.make_response(text)
        response['end_session'] = True
        return response

    def handle_local_intents(self, request: Request):
        pass


def _list_scenes():
    current_module = sys.modules[__name__]
    scenes = []
    for name, obj in inspect.getmembers(current_module):
        if inspect.isclass(obj) and issubclass(obj, Scene):
            scenes.append(obj)
    return scenes


SCENES = {
    scene.id(): scene for scene in _list_scenes()
}

DEFAULT_SCENE = Welcome
