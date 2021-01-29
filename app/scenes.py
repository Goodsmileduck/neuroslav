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

from models import Phrase, Question, User
import random, logging, settings


def in_session(request: Request, parameter):
    if request.state:
        param = request.state.get(STATE_REQUEST_KEY, {}).get(parameter, None)
        return param
    else:
        return None


def random_phrase(phrase_type):
    return random.choice(list(Phrase.objects.raw({'phrase_type': phrase_type}))).phrase


def give_random_question(request, user):
    MIXED_DIFFICULTY = 3
    raw_query = {
        'difficulty': {'$in': [user.difficulty, MIXED_DIFFICULTY]},
    }
    questions = Question.objects.raw(raw_query)
    for item in questions:
        print(item.user_question)
    question = random.choice(list(questions))
    return question


def current_user(request):
    try:
        application_id = request['session'].get('application').get('application_id')
        user = User.objects.get({'application_id': application_id})
        return user
    except Exception as ex:
        print('\nEXCEPTION:', ex)
        return None


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
        if intents.START_QUIZ in request.intents:
            return StartQuiz()


class Welcome(Main):
    def reply(self, request: Request):
        # User identification
        user = current_user(request)
        if user:
            first_time = False
        else:
            user = User(application_id=request['session']['application']['application_id']).save()
            first_time = True
        print('NEW USER'*first_time, user, user.application_id)

        if first_time:
            text = 'Здравствуй! Я нейросеть-экскурсовод по Великому Новгороду. Но, честно говоря, ' \
                   'после пожара в царской серверной я мало что помню.. ' \
                   'Кажется, меня зовут Нейрослав. Можешь помочь мне восстановить некоторые факты?'
        else:
            text = random_phrase(4)

        response = self.make_response(text, buttons=[
            button('Давай играть', hide=True)])
        return response

    def handle_local_intents(self, request: Request):
        user = current_user(request)

        match_answer = {'давай играть', 'да', 'начнем', 'играем'}
        user_request = request['request']['command']
        user_intent = request.intents
        print(user_intent)
        if user_request in match_answer or user_intent == "YANDEX.CONFIRM":
            if user.difficulty:
                return AskQuestion()
            else:
                return DifficultyChoice()


class DifficultyChoice(Main):
    def reply(self, request: Request):
        text = 'Какой уровень сложности ты хочешь?'

        response = self.make_response(text, buttons=[
            button('Простой', hide=True),
            button('Сложный', hide=True)]
        )
        return response

    def handle_local_intents(self, request: Request):
        user = current_user(request)
        if request['request']['command'] == 'простой':
            user.difficulty = 1
            user.save()
            return AskQuestion()
        elif request['request']['command'] == 'сложный':
            user.difficulty = 2
            user.save()
            return AskQuestion()


def give_fact_probability():
    # Returns if Interesting Fact should be given - True/False
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
        user = current_user(request)

        if self.give_clue:
            question_id = in_session(request, 'question_id')
            question = Question.objects.get({'_id': question_id})
            text = question.clue
            state = {
                'question_id': question.id,
                'clue_given': True,
            }
            self.give_clue = False

        elif self.wrong_answer:
            attempts = in_session(request, 'attempts')
            if not attempts:
                attempts = 1
            question_id = in_session(request, 'question_id')
            question = Question.objects.get({'_id': question_id})
            text = random_phrase(2)
            state = {
                'question_id': question.id,
                'attempts': attempts+1,
            }
            self.wrong_answer = False

        # Asking random question
        else:
            question = give_random_question(request=request, user=user)
            text = question.question
            # Give random confirmation phrase if last answer was right
            if self.give_confirmation:
                confirmation = random_phrase(1)
                text = confirmation + '\n' + text
            elif self.give_denial:
                denial = random_phrase(2)
                text = denial + '\n' + text
            state = {'clue_given': False, 'question_id': question.id}
            clue_button = True
            self.give_denial = False

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
        question = Question.objects.get({'_id': question_id})
        right_answers = [answer.answer for answer in question.right_answers]
        if request['request']['command'] in right_answers:
            if give_fact_probability():
                return GiveFact()
            return AskQuestion(give_confirmation=True)

        # Handle local intents (skip question, clue)
        if request['request']['command'] == 'подсказка':
            self.give_clue = True
            return self

        elif request['request']['command'] == 'пропустить':
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
        if request['request']['command'] == 'да':
            return AskQuestion(give_clue=True)
        elif request['request']['command'] == 'нет':
            return AskQuestion()


class GiveFact(Main):
    def reply(self, request: Request):
        question_id = in_session(request, 'question_id')
        question = Question.objects.get({'_id': question_id})
        continue_phrase = random_phrase(5)
        text = 'Верно!\n' + question.interesting_fact + '\n' + continue_phrase
        return self.make_response(text, buttons=[
            button('Да', hide=True),
            button('Нет', hide=True),
        ])

    def handle_local_intents(self, request: Request):
        if request['request']['command'] == 'да':
            return AskQuestion(give_confirmation=False)
        elif request['request']['command'] == 'нет':
            return Goodbye()


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
