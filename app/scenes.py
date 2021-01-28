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
from settings import VERSION

from models import Phrase, Question
import random

def in_session(request: Request, parameter):
    return request.get('state', {}).get(STATE_REQUEST_KEY, {}).get(parameter, None)

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
            'application_state': {'version': VERSION },
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

        for phrase in Phrase.objects.all():
            text += phrase.phrase + ' '

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
            button('Да', hide=True),
            button('Нет', hide=True),
        ])

    def handle_local_intents(self, request: Request):
        if request.get('request', {}).get('command', None) == 'да':
            return AskQuestion()


def give_fact():
    n = random.randint(0, 10)
    return n >= 7


class AskQuestion(Main):
    def reply(self, request: Request):
        # If there's question_id in session, going on with same question
        question_id = in_session(request, 'question_id')
        if question_id:
            question = Question.objects.raw({'_id': question_id}).first()
        # Else asking random question
        else:
            questions = Question.objects.all()
            question = random.choice(list(questions))
        text = question.question

        # Give random confirmation phrase last answer was right
        if in_session(request, 'give_confirmation'):
            confirmation = random.choice(list(Phrase.objects.raw({'phrase_type': 1}))).phrase
            text = confirmation + '\n' + text

        # Add right answers to buttons
        buttons = []
        for answer in question.possible_answers:
            buttons.append(button(answer.answer, hide=True))
        buttons += [button('Подсказка', hide=True), button('Пропустить', hide=True)]

        return self.make_response(text, state={
            'question_id': question.id,
            'give_confirmation': True,
            }, buttons=buttons)

    def handle_local_intents(self, request: Request):
        # Check if response contains right answer
        question_id = in_session(request, 'question_id')
        question = Question.objects.raw({'_id': question_id}).first()
        right_answers = [answer.answer for answer in question.right_answers]
        if request.get('request', {}).get('command', None) in right_answers:
            if give_fact():
                return GiveFact()
            return AskQuestion()

        # Handle local intents (skip question, clue)
        if request.get('request', {}).get('command', None) == 'подсказка':
            return GiveClue()
        elif request.get('request', {}).get('command', None) == 'пропустить':
            return SkipQuestion()

        # Assume answer as wrong
        return WrongAnswer()


class GiveClue(Main):
    def reply(self, request: Request):
        question_id = in_session(request, 'question_id')
        question = Question.objects.raw({'_id': question_id}).first()
        text = question.clue

        # Add right answers to buttons
        buttons = []
        for answer in question.possible_answers:
            buttons.append(button(answer.answer, hide=True))
        buttons += [button('Пропустить', hide=True)]

        return self.make_response(text, state={
            'question_id': question_id,
            'clue_given': True,
            'give_confirmation': True,
        }, buttons=buttons)

    def handle_local_intents(self, request: Request):
        # Check if response contains right answer
        question_id = in_session(request, 'question_id')
        question = Question.objects.raw({'_id': question_id}).first()
        right_answers = [answer.answer for answer in question.right_answers]
        if request.get('request', {}).get('command', None) in right_answers:
            if give_fact():
                return GiveFact()
            return AskQuestion()

        # Handle local intents (skip question, clue)
        if request.get('request', {}).get('command', None) == 'пропустить':
            return SkipQuestion()

        # Assume answer as wrong
        return WrongAnswer()


class SkipQuestion(Main):
    def reply(self, request: Request):
        if request.get('state', {}).get(STATE_REQUEST_KEY, {}).get('clue_given', None):
            # The clue has already given
            text = 'Подсказка уже была'
            return self.make_response(text)
            # redirect = AskQuestion()
            # redirect.reply(request)
        text = 'Дать подсказку?'
        return self.make_response(text, state={
            'question_id': in_session(request, 'question_id'),
        }, buttons=[
            button('Да', hide=True),
            button('нет', hide=True),
        ])

    def handle_local_intents(self, request: Request):
        if request.get('request', {}).get('command', None) == 'да':
            return GiveClue()
        elif request.get('request', {}).get('command', None) == 'нет':
            return AskQuestion()


class GiveFact(Main):
    def reply(self, request: Request):
        question_id = in_session(request, 'question_id')
        question = Question.objects.raw({'_id': question_id}).first()
        text = 'Верно!\n' + question.interesting_fact
        return self.make_response(text, state={
            'give_confirmation': False,
        }, buttons=[
            button('Дальше', hide=True),
        ])

    def handle_local_intents(self, request: Request):
        if request.get('request', {}).get('command', None) == 'дальше':
            return AskQuestion()


class WrongAnswer(Main):
    def reply(self, request: Request):
        question_id = in_session(request, 'question_id')
        question = Question.objects.raw({'_id': question_id}).first()
        text = 'Не угадал, попробуешь ещё раз?'
        if in_session(request, 'clue_given'):
            return self.make_response(text, state={
                'question_id': question_id,
            }, buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ])
        return self.make_response(text, buttons=[
            button('Да', hide=True),
            button('Нет', hide=True),
            button('Подскажи', hide=True),
        ])

    def handle_local_intents(self, request: Request):
        if request.get('request', {}).get('command', None) == 'да':
            return AskQuestion()
        elif request.get('request', {}).get('command', None) == 'нет':
            return Goodbye()
        elif request.get('request', {}).get('command', None) == 'подскажи':
            return GiveClue()


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
