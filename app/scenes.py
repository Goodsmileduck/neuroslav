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

from models import Phrase, Question, MIXED_DIFFICULTY, User, UserQuestion, LEVELS, PhraseType
import random
import logging, settings

from sounds import SoundFiles
import pymorphy2


def search_in_session(request: Request, parameter):
    if request.state:
        param = request.state.get(STATE_REQUEST_KEY, {}).get(parameter, None)
        return param
    else:
        return None


def give_random_question(request, user):
    all_user_questions = UserQuestion.objects.raw({'user': user._id})
    passed_questions_id = []
    for user_question in all_user_questions:
        passed_questions_id.append(user_question.question.id)
    logging.info(f"{request['session']['session_id']}: PASSED QUESTIONS - {passed_questions_id}")
    raw_query = {
        'difficulty': {'$in': [user.difficulty, MIXED_DIFFICULTY]},
        '_id': {'$nin': passed_questions_id},
    }
    questions = Question.objects.raw(raw_query)
    if not questions or questions.count() == 0:
        return None
    question = random.choice(list(questions))
    return question


def current_user(request):
    try:
        application_id = request['session'].get('application').get('application_id')
        user = User.objects.get({'application_id': application_id})
        return user
    except Exception as e:
        logging.error(f"{request['session']['session_id']}: EXCEPTION: {e}")
        return None


def word_in_plural(word, number):
    morph = pymorphy2.MorphAnalyzer()
    return morph.parse(word)[0].make_agree_with_number(number).word


def clear_text(text):
    punctuation = ',./\\!?<>'
    for character in punctuation:
        text = text.replace(character, '')
    while '  ' in text:
        text = text.replace('  ', ' ')
    return text.lower().strip()


def answer_is_right(request, question):
    try:
        user_reply = clear_text(request['request']['command'])
        right_answers = [answer.answer for answer in question.right_answers]
        # print(right_answers)
        return user_reply in right_answers
    except Exception as e:
        logging.error(f"{request['session']['session_id']}: ERROR looking of right answer. EXCEPTION:{e}" )
        return None


class UserMeaning:
    def __init__(self, request):
        self.request = request
        self.user_request = self.request['request'].get('command', None)
        self.user_intents = self.request.intents

    def is_answer_in_match_answers(self, match_answers):
        return self.user_request in match_answers

    def confirm(self):
        match_answers = ['да', 'конечно', 'пожалуй', 'да конечно', 'конечно да', 'давай', 'думаю да', 'хорошо']
        return intents.YANDEX_CONFIRM in self.user_intents or self.is_answer_in_match_answers(match_answers)

    def do_continue(self):
        match_answers = ['давай продолжим', 'продолжим', 'продолжаем', 'хочу продолжить', 'давай продолжать']
        return self.is_answer_in_match_answers(match_answers)

    def deny(self):
        match_answers = ['нет', 'не хочу', 'не надо', 'не думаю', 'наверное нет', 'конечно нет']
        return intents.YANDEX_REJECT in self.user_intents or self.is_answer_in_match_answers(match_answers)

    def dont_know(self):
        match_answers = ['не знаю', 'я не знаю', 'не уверен', 'я не уверен', 'без понятия']
        return self.is_answer_in_match_answers(match_answers)

    def lets_play(self):
        match_answers = ['давай играть', 'начнем', 'играем', 'сыграем', 'поехали', 'могу']
        return intents.START_QUIZ in self.user_intents or self.is_answer_in_match_answers(match_answers)

    def easy(self):
        match_answers = ['легкий', 'давай легкий', 'выбираю легкий', 'хочу легкий', 'простой', 'давай простой',
                         'хочу простой']
        return self.is_answer_in_match_answers(match_answers)

    def hard(self):
        match_answers = ['трудный', 'давай трудный', 'хочу трудный', 'выбираю трудный', 'сложный']
        return self.is_answer_in_match_answers(match_answers)

    def give_clue(self):
        match_answers = ['подскажи', 'дай подсказку', 'хочу подсказку', 'прошу подсказку', 'подсказка',
                         'подскажи пожалуйста', 'помоги', 'повтори подсказку']
        return intents.CLUE in self.user_intents or self.is_answer_in_match_answers(match_answers)

    def skip_question(self):
        match_answers = ['пропустить', 'пропусти вопрос', 'пропусти', 'следующий вопрос', 'следующий',
                         'давай следующий', 'дальше', 'далее', 'давай дальше']
        return self.is_answer_in_match_answers(match_answers)

    def repeat(self):
        match_answers = ['повтори', 'повтори пожалуйста', 'ещё раз', 'скажи ещё раз', 'давай ещё раз', 'повторить',
                         'можешь повторить']
        return intents.START_QUIZ in self.user_intents or self.is_answer_in_match_answers(match_answers)


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
        next_scene = self.handle_global_intents(request)
        if next_scene is None:
            next_scene = self.handle_local_intents(request)
        return next_scene

    @abstractmethod
    def handle_global_intents(self, request):
        raise NotImplementedError()

    @abstractmethod
    def handle_local_intents(self, request: Request) -> Optional[str]:
        raise NotImplementedError()

    def fallback(self, request: Request):
        return self.make_response('Извините, я вас не понимаю. Пожалуйста, попробуйте переформулировать вопрос.')

    def make_audio_tts(self, audio_file_name, text='', tts=None):
        if tts is None:
            tts = text
        sound_tag = f"<speaker audio='{audio_file_name.value}'> "
        return sound_tag + tts

    def make_response(self, text, tts=None, card=None, state=None, buttons=None, directives=None, audio_file_name = None):
        if audio_file_name is not None:
            tts = self.make_audio_tts(audio_file_name, text, tts)

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
        user_meant = UserMeaning(request)
        if intents.YANDEX_HELP in request.intents and not user_meant.give_clue():
            return GetHelp()
        elif intents.YANDEX_WHAT_CAN_YOU_DO in request.intents:
            return WhatCanYouDo()
        elif intents.EXIT in request.intents:
            return Goodbye()
        elif intents.CHANGE_DIFFICULTY in request.intents:
            return DifficultyChoice()
        else:
            return None


class Welcome(Main):
    def reply(self, request: Request):
        # User identification
        user = current_user(request)
        if user:
            first_time = False
            logging.info(f"User come back. application_id: {user.application_id} sessions: {request['session']['session_id']}")
        else:
            user = User(application_id=request['session'].get('application').get('application_id')).save()
            first_time = True
            logging.info(f"New user. application_id: {user.application_id} session: {request['session']['session_id']}")

        sound_file_name = None
        gained_new_level, level, points = user.gained_new_level()
        if first_time or points < 1:
            text = 'Здравствуй! Я нейросеть-экскурсовод по Великому Новгороду. Но, честно говоря, ' \
                   'после пожара в царской серверной я мало что помню.. ' \
                   'Кажется, меня зовут Нейрослав. Можешь помочь мне восстановить некоторые факты?'
        else:
            word = word_in_plural('вопрос', points)
            text = Phrase.give_greeting() % {'number': points,
                                                         'question': word,
                                                         'level': level}

        # text += ' Версия: ' + VERSION

        response = self.make_response(
            text,
            buttons=[button('Давай играть', hide=True)],
            audio_file_name=sound_file_name
        )
        return response

    def handle_local_intents(self, request: Request):
        user = current_user(request)
        user_meant = UserMeaning(request)

        if user_meant.lets_play() or user_meant.confirm():
            if user.difficulty is not None:
                return AskQuestion()
            else:
                return DifficultyChoice()

        return Goodbye()


class DifficultyChoice(Main):
    def reply(self, request: Request):
        text = 'Есть легкий и трудный уровни сложности. Какой ты выберешь?'

        response = self.make_response(text, buttons=[
            button('Легкий', hide=True),
            button('Трудный', hide=True)]
        )
        return response

    def handle_local_intents(self, request: Request):
        user = current_user(request)
        user_meant = UserMeaning(request)
        if user_meant.easy():
            user.difficulty = 1
            user.save()
            return AskQuestion()
        elif user_meant.hard():
            user.difficulty = 2
            user.save()
            return AskQuestion()
#        elif intents.CHANGE_DIFFICULTY in request.intents:
#            user.difficulty = 2
#            user.save()
#            return AskQuestion()


def give_fact_probability():
    # Returns if Interesting Fact should be given - True/False
    # n = random.randint(0, 10)
    # return n >= 7
    return True


class AskQuestion(Main):
    def __init__(self, give_clue=False, give_confirmation=False, give_denial=False, repeat=False):
        super(AskQuestion, self).__init__()
        self.give_clue = give_clue
        self.give_confirmation = give_confirmation
        self.give_denial = give_denial
        self.wrong_answer = False
        self.repeat = repeat

    def reply(self, request: Request):
        clue_button = False
        user = current_user(request)
        tts = ''

        if self.give_clue:
            attempts = search_in_session(request, 'attempts')
            if not attempts:
                attempts = 1
            question_id = search_in_session(request, 'question_id')
            question = Question.objects.get({'_id': question_id})
            text = question.clue
            state = {
                'question_id': question.id,
                'clue_given': True,
                'attempts': attempts,
            }

        # Wrong answer, giving one more attempt
        elif self.wrong_answer:
            attempts = search_in_session(request, 'attempts')
            if not attempts:
                attempts = 1
            question_id = search_in_session(request, 'question_id')
            question = Question.objects.get({'_id': question_id})
            text = Phrase.give_you_are_wrong() + '\n' + Phrase.give_try_again()
            state = {
                'question_id': question.id,
                'attempts': attempts+1,
                'clue_given': search_in_session(request, 'clue_given'),
            }
            self.wrong_answer = False
        # Asked for repeat question
        elif self.repeat:
            question_id = search_in_session(request, 'question_id')
            question = Question.objects.get({'_id': question_id})
            text = question.question
            if question.tts and question.tts != '':
                tts = question.tts
            else:
                tts = text
            state = {
                'question_id': question.id,
                'attempts': search_in_session(request, 'attempts'),
                'clue_given': search_in_session(request, 'clue_given'),
            }
        # Asking random question
        else:
            question = give_random_question(request=request, user=user)
            if not question:
                return self.make_response('Поздравляю, ты прошёл все вопросы!!')

            text = question.question
            if question.tts and question.tts != '':
                tts = question.tts
            else:
                tts = text
            # Give random confirmation phrase if last answer was right
            if self.give_confirmation:
                confirmation = Phrase.give_you_are_right()
                next_question = Phrase.give_next_question()
                text = confirmation + '\n' + next_question + '\n' + text
                tts = confirmation + ' - ' + next_question + ' - ' + tts
            # Give random denial phrase if last answer was wrong
            elif self.give_denial:
                denial = Phrase.give_you_are_wrong()
                try_next_question = Phrase.give_next_question()
                text = denial + '\n' + try_next_question + '\n' + text
                tts = denial + ' - ' + try_next_question + ' - ' + tts
            state = {'clue_given': False, 'question_id': question.id}
            clue_button = True
            self.give_denial = False

        if tts == '':
            tts = text
        # Add right answers to buttons
        buttons = []
        if user.difficulty == 1:
            number_of_answers = len(question.possible_answers)
            for i, answer in enumerate(question.possible_answers):
                buttons.append(button(answer.answer, hide=True))
                if i != number_of_answers - 1:
                    tts += ' - ' + answer.answer + ','
                else:
                    tts += ' - или ' + answer.answer + '?'
        if clue_button or (not search_in_session(request, 'clue_given') and not self.give_clue):
            buttons.append(button('Подсказка', hide=True))
        buttons.append(button('Пропустить', hide=True))

        return self.make_response(text, state=state, buttons=buttons, tts=tts)

    def handle_local_intents(self, request: Request):
        user = current_user(request)
        user_meant = UserMeaning(request)
        question_id = search_in_session(request, 'question_id')
        question = Question.objects.get({'_id': question_id})
        logging.info(f"{request['session']['session_id']}: Question #{question_id} - {question}")

        # Check if response contains right answer
        if answer_is_right(request, question):
            UserQuestion(user=user, question=question_id, passed=True).save()
            give_fact = question.interesting_fact is not None and question.interesting_fact != '' and give_fact_probability()
            gained_level, level, points = user.gained_new_level()
            logging.info(f"{request['session']['session_id']}: GAINED_NEW_LEVEL - {gained_level} {level}")
            if gained_level:
                return LevelCongratulation(level=level, points=points, interesting_fact=give_fact)
            if give_fact:
                return GiveFact()
            return AskQuestion(give_confirmation=True)

        # Handle local intents (skip question, clue)
        elif user_meant.give_clue():
            if search_in_session(request, 'clue_given'):
                return YouHadClue()
            self.give_clue = True
            return self

        elif user_meant.skip_question() or user_meant.dont_know():
            if not search_in_session(request, 'clue_given'):
                return SkipQuestion()
            UserQuestion(user=user, question=question_id, passed=False).save()
            return AskQuestion()

        elif user_meant.repeat():
            return AskQuestion(repeat=True)
        # Handle global intents !!!

        # Assume answer as wrong
        attempts = search_in_session(request, 'attempts')
        if attempts and attempts >= settings.MAX_ATTEMPTS:
            return AskQuestion(give_denial=True)
        logging.warning(f"{request['session']['session_id']}: ATTEMPTS - {attempts}")
        self.wrong_answer = True
        return self


class YouHadClue(Main):
    def reply(self, request: Request):
        text = Phrase.give_you_had_clue_ask()
        attempts = search_in_session(request, 'attempts')
        if not attempts:
            attempts = 1
        state = {
            'question_id': search_in_session(request, 'question_id'),
            'attempts': attempts,
            'clue_given': True,
        }
        return self.make_response(text, state=state, buttons=[
            button('Да', hide=True),
            button('нет', hide=True),
        ])

    def handle_local_intents(self, request: Request):
        user = current_user(request)
        question_id = search_in_session(request, 'question_id')
        user_meant = UserMeaning(request)
        if user_meant.confirm() or user_meant.give_clue():
            return AskQuestion(give_clue=True)
        elif user_meant.deny() or user_meant.skip_question():
            return AskQuestion(repeat=True)


class LevelCongratulation(Main):
    def __init__(self, level=LEVELS[0], points=0, interesting_fact=False):
        super(LevelCongratulation, self).__init__()
        self.level = level
        self.points = points
        self.interesting_fact = interesting_fact

    def reply(self, request: Request):
        word = word_in_plural('вопрос', self.points)
        text = Phrase.give_new_level_congratulation() % {'number': self.points,
                                                                     'question': word,
                                                                     'level': self.level}
        if self.interesting_fact:
            question_id = search_in_session(request, 'question_id')
            question = Question.objects.get({'_id': question_id})
            confirmation_phrase = Phrase.give_you_are_right()
            text = confirmation_phrase + '\n' + question.interesting_fact + '\n' + text
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('нет', hide=True),
            ],
            audio_file_name=SoundFiles.GREETING
        )

    def handle_local_intents(self, request: Request):
        user_meant = UserMeaning(request)
        if user_meant.confirm() or user_meant.do_continue():
            return AskQuestion()
        else:
            return Goodbye()


class SkipQuestion(Main):
    def reply(self, request: Request):
        text = Phrase.give_offer_clue()
        attempts = search_in_session(request, 'attempts')
        if not attempts:
            attempts = 1
        state = {
            'question_id': search_in_session(request, 'question_id'),
            'attempts': attempts,
        }
        return self.make_response(text, state=state, buttons=[
            button('Да', hide=True),
            button('нет', hide=True),
        ])

    def handle_local_intents(self, request: Request):
        user = current_user(request)
        question_id = search_in_session(request, 'question_id')
        user_meant = UserMeaning(request)
        if user_meant.confirm() or user_meant.skip_question():
            return AskQuestion(give_clue=True)
        elif user_meant.deny():
            UserQuestion(user=user, question=question_id, passed=False).save()
            return AskQuestion()


class GiveFact(Main):
    def reply(self, request: Request):
        question_id = search_in_session(request, 'question_id')
        question = Question.objects.get({'_id': question_id})
        confirmation_phrase = Phrase.give_you_are_right()
        continue_phrase = Phrase.give_continue_ask()
        text = confirmation_phrase + '\n' + question.interesting_fact + '\n' + continue_phrase
        return self.make_response(text, buttons=[
            button('Да', hide=True),
            button('Нет', hide=True),
        ])

    def handle_local_intents(self, request: Request):
        user = current_user(request)
        user_meant = UserMeaning(request)
        if user_meant.confirm() or user_meant.do_continue():
            gained_level, level, points = user.gained_new_level()
            logging.info(f"Gained level: {gained_level}, LEVEL: {level}, points: {points}")
            print(f"Gained level: {gained_level}, LEVEL: {level}, points: {points}")
            if gained_level:
                return LevelCongratulation(level=level, points=points)
            return AskQuestion(give_confirmation=False)
        elif user_meant.deny():
            return Goodbye()


class GetHelp(Main):
    def reply(self, request: Request):
        text = 'Чтобы помочь мне восстановить данные для моих нейронов, ' \
        'Тебе нужно отвечать на мои вопросы. Есть два режима сложности - легкий и трудный. '\
        'Я также могу поискать подсказку в фрагментах памяти или '\
        'ты можешь пропустить вопрос если не знаешь ответа. '

        if request.state is not None:
            attempts = search_in_session(request, 'attempts')
            question_id = search_in_session(request, 'question_id')
            clue_given = search_in_session(request, 'clue_given')
            state = {
                'question_id': question_id,
                'clue_given': clue_given,
                'attempts': attempts,
            }
            end_text = 'Продолжаем?'

            return self.make_response(text+end_text, state=state, buttons=[button('Да', hide=True)])
        else:
            end_text = 'Хочешь попробовать?'
            return self.make_response(text+end_text, buttons=[button('Да', hide=True)])

    def handle_local_intents(self, request: Request):
        user = current_user(request)
        user_meant = UserMeaning(request)
        user_intent = request.intents
        logging.info(f"{request['session']['session_id']}: User intent - {user_intent}")
        if user_meant.lets_play() or user_meant.confirm():
            if user.difficulty:
                return AskQuestion()
            else:
                return DifficultyChoice()


class WhatCanYouDo(Main):
    def reply(self, request: Request):
        text = 'Я нейросеть-гид по Великому Новгороду. ' \
        'Моя база данных повреждена и мне нужна помощь в восставновлении давнных. '\
        'Готов ли ты помочь мне?'
        return self.make_response(text, buttons=[
            button('Я готов', hide=True)])
    
    def handle_local_intents(self, request: Request):
        user = current_user(request)
        user_meant = UserMeaning(request)
        user_intent = request.intents
        logging.info(f"{request['session']['session_id']}: User intent - {user_intent}")
        if user_meant.lets_play() or user_meant.confirm():
            if user.difficulty:
                return AskQuestion()
            else:
                return DifficultyChoice()


class Goodbye(Main):
    def reply(self, request: Request):
        text = 'Буду рад видеть тебя снова! Скажи ПОКА чтобы выйти из навыка.'
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
