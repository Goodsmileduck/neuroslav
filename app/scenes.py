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
import random, logging, settings

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
        return self.make_response('Извините, я вас не понимаю. Пожалуйста, попробуйте переформулировать вопрос.')

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

        #for phrase in Phrase.objects.all():
        #    text += phrase.phrase + ' '

        response = self.make_response(text, buttons=[
            button('Давай играть', hide=True)])
        return response

    def handle_local_intents(self, request: Request):
        match_answer = {'давай играть', 'да', 'начнем', 'играем'}
        user_request = request.get('request', {}).get('command', None)
        user_intent = request.get('request', {}).get('nlu', {}).get('intent', {})
        if user_request in answer or user_intent == "YANDEX.CONFIRM":
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
    def __init__(self, give_clue=False, give_confirmation=False, give_denial=False):
        super(AskQuestion, self).__init__()
        self.give_clue = give_clue
        self.give_confirmation = give_confirmation
        self.give_denial = give_denial
        self.wrong_answer = False

    def reply(self, request: Request):
        clue_button = False

        if self.give_clue:
            question_id = in_session(request, 'question_id')
            question = Question.objects.raw({'_id': question_id}).first()
            text = question.clue
            state = {
                'question_id': question.id,
                'clue_given': True,
            }

        elif self.wrong_answer:
            attempts = in_session(request, 'attempts')
            if not attempts:
                attempts = 1
            question_id = in_session(request, 'question_id')
            question = Question.objects.raw({'_id': question_id}).first()
            text = random.choice(list(Phrase.objects.raw({'phrase_type': 2}))).phrase
            state = {
                'question_id': question.id,
                'attempts': attempts+1,
            }

        # Asking random question
        else:
            questions = Question.objects.all()
            question = random.choice(list(questions))
            text = question.question
            # Give random confirmation phrase if last answer was right
            if self.give_confirmation:
                confirmation = random.choice(list(Phrase.objects.raw({'phrase_type': 1}))).phrase
                text = confirmation + '\n' + text
            elif self.give_denial:
                denial = random.choice(list(Phrase.objects.raw({'phrase_type': 2}))).phrase
                text = denial + '\n' + text
            state = {'clue_given': False, 'question_id': question.id}
            clue_button = True

        # Add right answers to buttons
        buttons = []
        for answer in question.possible_answers:
            buttons.append(button(answer.answer, hide=True))
        if clue_button or (not in_session(request, 'clue_given') and not self.give_clue):
            buttons.append(button('Подсказка', hide=True))
        buttons.append(button('Пропустить', hide=True))

        return self.make_response(text, state=state, buttons=buttons)


    def handle_local_intents(self, request: Request):
        # Check if response contains right answer
        question_id = in_session(request, 'question_id')
        question = Question.objects.raw({'_id': question_id}).first()
        right_answers = [answer.answer for answer in question.right_answers]
        if request.get('request', {}).get('command', None) in right_answers:
            if give_fact():
                return GiveFact()
            return AskQuestion(give_confirmation=True)

        # Handle local intents (skip question, clue)
        if request.get('request', {}).get('command', None) == 'подсказка':
            self.give_clue = True
            return self

        elif request.get('request', {}).get('command', None) == 'пропустить':
            if not in_session(request, 'clue_given'):
                return SkipQuestion()
            return AskQuestion()

        # Handle global intents !!!

        # Assume answer as wrong
        attempts = in_session(request, 'attempts')
        if attempts and attempts >= settings.MAX_ATTEMPTS:
            return AskQuestion(give_denial=True)
        logging.warning(f'ATTEMPTS: {attempts}')
        self.wrong_answer = True
        return self


class SkipQuestion(Main):
    def reply(self, request: Request):
        text = 'Дать подсказку?'
        return self.make_response(text, state={
            'question_id': in_session(request, 'question_id'),
        }, buttons=[
            button('Да', hide=True),
            button('нет', hide=True),
        ])

    def handle_local_intents(self, request: Request):
        if request.get('request', {}).get('command', None) == 'да':
            return AskQuestion(give_clue=True)
        elif request.get('request', {}).get('command', None) == 'нет':
            return AskQuestion()


class GiveFact(Main):
    def reply(self, request: Request):
        question_id = in_session(request, 'question_id')
        question = Question.objects.raw({'_id': question_id}).first()
        text = 'Верно!\n' + question.interesting_fact
        return self.make_response(text, buttons=[
            button('Дальше', hide=True),
        ])

    def handle_local_intents(self, request: Request):
        if request.get('request', {}).get('command', None) == 'дальше':
            return AskQuestion(give_confirmation=False)


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
