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


def clear_not_passed_questions(user):
    not_passed_user_questions = UserQuestion.objects.raw({'user': user._id, 'passed': False})
    not_passed_user_questions.delete()


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
        logging.debug(f"{request['session']['session_id']}: User does not exist. {e}")
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
        AVOID_WORDS = ('я', 'думаю', 'наверное', 'кажется', 'это', 'был', 'была', 'были', 'мне')
        text_list = user_reply.split()
        user_reply = ' '.join([word for word in text_list if word not in AVOID_WORDS])
        right_answers = [answer.answer for answer in question.right_answers]
        # print(right_answers)
        return user_reply in right_answers or user_reply in settings.CHEATS
    except Exception as e:
        logging.error(f"{request['session']['session_id']}: ERROR looking of right answer. EXCEPTION:{e}" )
        return None


def handle_fallbacks(request, ReturnScene, **kwargs):
    # Catch fallbacks, needs a ReturnScene class, which has 'fallback' parameter
    fallback = search_in_session(request, 'fallback')
    if fallback:
        if fallback < 2:
            return ReturnScene(fallback=fallback+1, **kwargs)
        else:
            return Goodbye(fallback=1)
    return ReturnScene(fallback=1, **kwargs)


def give_fact_probability():
    # Returns if Interesting Fact should be given - True/False
    # n = random.randint(0, 10)
    # return n >= 7
    return True


class UserMeaning:
    def __init__(self, request):
        self.request = request
        self.user_request = self.request['request'].get('command', None)
        self.user_intents = self.request.intents

    def is_answer_in_match_answers(self, match_answers):
        cleaned = self.user_request.replace('пожалуйста', '')
        cleaned = clear_text(cleaned)
        return cleaned in match_answers

    def confirm(self):
        match_answers = ['да', 'конечно', 'пожалуй', 'да конечно', 'конечно да', 'давай', 'думаю да', 'хорошо', 'я готов', 'готов', 'да да', 'ага', 'идём', 'идем']
        return intents.YANDEX_CONFIRM in self.user_intents or self.is_answer_in_match_answers(match_answers)

    def do_continue(self):
        match_answers = ['давай продолжим', 'продолжим', 'продолжаем', 'хочу продолжить', 'давай продолжать', 'продолжай', 'давай продолжай', 'продолжи', 'продолжить', 'продолжать']
        return self.is_answer_in_match_answers(match_answers)

    def deny(self):
        match_answers = ['нет', 'не хочу', 'не надо', 'не думаю', 'наверное нет', 'конечно нет', 'не надо', 'нет нет']
        return intents.YANDEX_REJECT in self.user_intents or self.is_answer_in_match_answers(match_answers)

    def dont_know(self):
        match_answers = ['не знаю', 'я не знаю', 'не уверен', 'я не уверен', 'без понятия', 'даже не знаю']
        return self.is_answer_in_match_answers(match_answers)

    def lets_play(self):
        match_answers = ['давай играть', 'начнем', 'играем', 'сыграем', 'поехали', 'могу']
        return intents.START_QUIZ in self.user_intents or self.is_answer_in_match_answers(match_answers)

    def easy(self):
        match_answers = ['легкий', 'давай легкий', 'выбираю легкий', 'хочу легкий', 'простой', 'давай простой',
                         'хочу простой', 'легкий уровень', 'простой уровень']
        return self.is_answer_in_match_answers(match_answers)

    def hard(self):
        match_answers = ['трудный', 'давай трудный', 'хочу трудный', 'выбираю трудный', 'сложный', 'сложный уровень',
                         'трудный уровень']
        return self.is_answer_in_match_answers(match_answers)

    def give_clue(self):
        match_answers = ['подскажи', 'дай подсказку', 'хочу подсказку', 'прошу подсказку', 'подсказка',
                         'подскажи пожалуйста', 'помоги', 'повтори подсказку', 'подсказку', 'подсказку бы']
        return intents.CLUE in self.user_intents or self.is_answer_in_match_answers(match_answers)

    def skip_question(self):
        match_answers = ['пропустить', 'пропусти вопрос', 'пропусти', 'следующий вопрос', 'следующий',
                         'давай следующий', 'дальше', 'далее', 'давай дальше']
        return self.is_answer_in_match_answers(match_answers)

    def repeat(self):
        match_answers = ['повтори', 'ещё раз', 'еще раз', 'скажи ещё раз', 'давай ещё раз', 'повторить',
                         'можешь повторить', 'повтори вопрос']
        return intents.YANDEX_REPEAT in self.user_intents or self.is_answer_in_match_answers(match_answers)

    def repeat_options(self):
        match_answers = ['повтори варианты', 'пожалуйста повтори варианты', 'скажи варинаты отвеов',
                         'повтори варианты ответов', 'повтори ответы', 'какие варианты', 'какие варианты ответов',
                         'какие варианты ответа', 'варианты ответа', 'повтори пожалуйста варианты',
                         'повтори пожалуйста варианты ответов', 'какие есть варианты']
        return intents.YANDEX_REPEAT in self.user_intents or self.is_answer_in_match_answers(match_answers)


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
    def __init__(self, fallback=0):
        super(Main, self).__init__()
        self.fallback = fallback

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
        elif intents.GET_LEVEL in request.intents:
            return GetLevel()
        elif request['request']['command'] == "версия":
             return GetVersion()
        else:
            return None


class Welcome(Main):
    def reply(self, request: Request):
        sound_file_name = ''
        card = None

        if request['request']['command'] == "ping":
            response_pong = self.make_response("pong")
            return response_pong

        if self.fallback == 1:
            text = Phrase.give_fallback_general()
        elif self.fallback > 1:
            text = Phrase.give_fallback_2_begin() + ' Пожалуйста, ответь да или нет, - готов ли ты восстановить мне некоторые факты?'
        else:
            # User identification
            user = current_user(request)
            if user:
                first_time = False
                logging.info(f"User come back. application_id: {user.application_id} sessions: {request['session']['session_id']}")
                sound_file_name = SoundFiles.WELCOME_SECOND.value
            else:
                user = User(application_id=request['session'].get('application').get('application_id')).save()
                sound_file_name = SoundFiles.WELCOME_FIRST.value
                first_time = True
                logging.info(f"New user. application_id: {user.application_id} session: {request['session']['session_id']}")

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
            card = {
                'type': 'BigImage',
                'image_id': settings.WELCOME_IMAGE,
                'description': text,
            }

        response = self.make_response(
            text,
            tts=sound_file_name + text,
            buttons=[button('Давай играть', hide=True)],
            state={'fallback': self.fallback},
            card=card
        )
        return response

    def handle_local_intents(self, request: Request):
        user = current_user(request)

        user_meant = UserMeaning(request)

        if user_meant.lets_play() or user_meant.confirm():
            if user.difficulty is not None:
                return AskQuestion(lets_play=True)
            else:
                return DifficultyChoice()
        elif user_meant.deny():
            return Goodbye()
        elif user_meant.repeat():
            return Welcome()

        return handle_fallbacks(request, Welcome)


class DifficultyChoice(Main):
    def reply(self, request: Request):
        if self.fallback == 1:
            text = Phrase.give_fallback_general()
        elif self.fallback > 1:
            text = Phrase.give_fallback_2_begin() + ' Скажи, пожалуйста, какой уровень сложности ты выбираешь: лёгкий или трудный?'
        else:
            text = 'Есть легкий и трудный уровни сложности. Какой ты выберешь?'

        state = {'fallback': self.fallback}
        response = self.make_response(text, buttons=[
            button('Легкий', hide=True),
            button('Трудный', hide=True)
        ], state=state
        )
        return response

    def handle_local_intents(self, request: Request):
        user = current_user(request)
        user_meant = UserMeaning(request)
        if user_meant.easy():
            user.difficulty = 1
            user.save()
            return AskQuestion(lets_play=True)
        elif user_meant.hard():
            user.difficulty = 2
            user.save()
            return AskQuestion(lets_play=True)
        elif user_meant.repeat():
            return DifficultyChoice()
        return handle_fallbacks(request, DifficultyChoice)


class AskQuestion(Main):
    def __init__(self, give_clue=False, give_confirmation=False, give_denial=False, repeat=False, repeat_options=False, lets_play=False):
        super(AskQuestion, self).__init__()
        self.give_clue = give_clue
        self.give_confirmation = give_confirmation
        self.give_denial = give_denial
        self.wrong_answer = False
        self.repeat = repeat
        self.repeat_options = repeat_options
        self.lets_play = lets_play

    def reply(self, request: Request):
        clue_button = False
        user = current_user(request)
        tts = ''
        text = ''

        if self.give_clue:
            attempts = search_in_session(request, 'attempts')
            if not attempts:
                attempts = 1
            question_id = search_in_session(request, 'question_id')
            question = Question.objects.get({'_id': question_id})
            text = question.clue
            tts = question.clue_tts
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
        # Asked to repeat options
        elif self.repeat_options:
            question_id = search_in_session(request, 'question_id')
            question = Question.objects.get({'_id': question_id})
            text = question.question
            tts = '- '
            state = {
                'question_id': question.id,
                'attempts': search_in_session(request, 'attempts'),
                'clue_given': search_in_session(request, 'clue_given'),
            }
        # Give random question
        else:
            question = give_random_question(request=request, user=user)
            if not question:
                clear_not_passed_questions(user)
                question = give_random_question(request=request, user=user)
                if not question:
                    return self.make_response('Святые транзисторы, это просто невероятно, ты прошёл все вопросы! Поздравляю! \n'
                                              'Я чувствую, что моя нейросеть полностью восстановилась! Возвращайся чуть позже для улучшения точности моей базы данных. \nСПАСИБО!!!')
            gained_level, level, points = user.gained_new_level()
            if self.lets_play:
                if points < 1:
                    text = tts = "Моя кратковременная память ограничена. Я смогу проверить только 2 ответа на каждый вопрос. У тебя всегда есть возможность взять подсказку, пропустить или повторить вопрос.\nНачнём!\n"
                else:
                    text = tts = Phrase.give_lets_play() + '\n'
            text += question.question
            if question.tts and question.tts != '':
                tts += question.tts
            else:
                tts += question.question
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
                if not self.give_clue and not question.possible_answers_tts:
                    if i != number_of_answers - 1:
                        tts += ' - ' + answer.answer + ','
                    else:
                        tts += ' - или ' + answer.answer + '?'
            if not self.give_clue and question.possible_answers_tts:
                number_of_answers_tts = len(question.possible_answers_tts)
                for i, answer_tts in enumerate(question.possible_answers_tts):
                    if i != number_of_answers_tts - 1:
                        tts += ' - ' + answer_tts.answer + ','
                    else:
                        tts += ' - или ' + answer_tts.answer + '?'
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

        elif user.difficulty == 1 and user_meant.repeat_options():
            return AskQuestion(repeat_options=True)

        # Assume answer as wrong
        attempts = search_in_session(request, 'attempts')
        if attempts and attempts >= settings.MAX_ATTEMPTS:
            UserQuestion(user=user, question=question_id, passed=False).save()
            return AskQuestion(give_denial=True)
        logging.warning(f"{request['session']['session_id']}: ATTEMPTS - {attempts}")
        self.wrong_answer = True
        return self


class YouHadClue(Main):
    def reply(self, request: Request):
        if self.fallback == 1:
            text = Phrase.give_fallback_general()
        elif self.fallback > 1:
            text = Phrase.give_fallback_2_begin() + ' Ответь, пожалуйста, да или нет, - хочешь, чтобы я повторил подсказку?'
        else:
            text = Phrase.give_you_had_clue_ask()
        attempts = search_in_session(request, 'attempts')
        if not attempts:
            attempts = 1
        state = {
            'question_id': search_in_session(request, 'question_id'),
            'attempts': attempts,
            'clue_given': True,
            'fallback': self.fallback,
        }
        return self.make_response(text, state=state, buttons=[
            button('Да', hide=True),
            button('нет', hide=True),
        ])

    def handle_local_intents(self, request: Request):
        user = current_user(request)
        question_id = search_in_session(request, 'question_id')
        user_meant = UserMeaning(request)
        if user_meant.confirm() or user_meant.give_clue() or user_meant.repeat():
            return AskQuestion(give_clue=True)
        elif user_meant.deny() or user_meant.skip_question():
            return AskQuestion(repeat=True)
        elif user_meant.repeat():
            return YouHadClue()

        return handle_fallbacks(request, YouHadClue)


class LevelCongratulation(Main):
    def __init__(self, level=LEVELS[0], points=0, interesting_fact=False, fallback=0, give_confirmation=True, repeat=False):
        super(LevelCongratulation, self).__init__(fallback)
        self.level = level
        self.points = points
        self.interesting_fact = interesting_fact
        self.give_confirmation = give_confirmation
        self.repeat = repeat

    def reply(self, request: Request):
        word = word_in_plural('вопрос', self.points)
        card = None
        audio_file_name = ''
        question_id = search_in_session(request, 'question_id')
        if self.fallback == 1:
            text = Phrase.give_fallback_general()
        elif self.fallback > 1:
            text = Phrase.give_fallback_2_begin() + ' Ответь, пожалуйста, да или нет, - хочешь продолжить?'
        else:
            text = Phrase.give_new_level_congratulation() % {'number': self.points,
                                                             'question': word,
                                                             'level': self.level}
            if not self.repeat:
                audio_file_name = SoundFiles.GREETING.value
            if self.interesting_fact:
                question = Question.objects.get({'_id': question_id})
                text = question.interesting_fact + '\n' + text
            if self.give_confirmation:
                confirmation_phrase = Phrase.give_you_are_right()
                text = confirmation_phrase + '\n' + text
            if self.interesting_fact and question.interesting_fact_pic_id and question.interesting_fact_pic_id != '':
                card = {
                    'type': 'BigImage',
                    'image_id': question.interesting_fact_pic_id,
                    'description': text,
                }
        repeat_text = search_in_session(request, 'repeat_text')
        if repeat_text is None:
            repeat_text = text
        return self.make_response(
            text,
            tts=audio_file_name + text,
            buttons=[button('Да', hide=True), button('Нет', hide=True)],
            state={'fallback': self.fallback,
                   'interesting_fact': self.interesting_fact,
                   'question_id': question_id,
                   'level': self.level,
                   'points': self.points},
            card=card
        )

    def handle_local_intents(self, request: Request):
        user_meant = UserMeaning(request)
        if user_meant.confirm() or user_meant.do_continue():
            return AskQuestion(give_confirmation=False)
        elif user_meant.deny():
            return Goodbye()
        elif user_meant.repeat():
            return LevelCongratulation(interesting_fact=search_in_session(request, 'interesting_fact'),
                                       give_confirmation=False,
                                       level=search_in_session(request, 'level'),
                                       points=search_in_session(request, 'points'),
                                       repeat=True)
        return handle_fallbacks(request, LevelCongratulation,
                                interesting_fact=search_in_session(request, 'interesting_fact'),
                                give_confirmation=False,
                                level=search_in_session(request, 'level'),
                                points=search_in_session(request, 'points')
                                )


class SkipQuestion(Main):
    def reply(self, request: Request):
        if self.fallback == 1:
            text = Phrase.give_fallback_general()
        elif self.fallback > 1:
            text = Phrase.give_fallback_2_begin() + ' Пожалуйста, ответь да или нет, - дать подсказку??'
        else:
            text = Phrase.give_offer_clue()
        attempts = search_in_session(request, 'attempts')
        if not attempts:
            attempts = 1
        state = {
            'question_id': search_in_session(request, 'question_id'),
            'attempts': attempts,
            'fallback': self.fallback,
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
            UserQuestion(user=user, question=question_id, passed=False).save()
            return AskQuestion()
        elif user_meant.repeat():
            return SkipQuestion()
        return handle_fallbacks(request, SkipQuestion)


class GiveFact(Main):
    def __init__(self, fallback=0, give_confirmation=True):
        super(GiveFact, self).__init__(fallback)
        self.give_confirmation = give_confirmation

    def reply(self, request: Request):
        card = None
        question_id = search_in_session(request, 'question_id')
        if self.fallback == 1:
            text = Phrase.give_fallback_general()
        elif self.fallback > 1:
            text = Phrase.give_fallback_2_begin() + ' Пожалуйста, ответь да или нет, - хочешь продолжить?'
        else:
            question = Question.objects.get({'_id': question_id})
            continue_phrase = Phrase.give_continue_ask()
            text = question.interesting_fact + '\n' + continue_phrase
            if self.give_confirmation:
                confirmation_phrase = Phrase.give_you_are_right()
                text = confirmation_phrase + '\n' + text
            if question.interesting_fact_pic_id and question.interesting_fact_pic_id != '':
                card = {
                    'type': 'BigImage',
                    'image_id': question.interesting_fact_pic_id,
                    'description': text,
                }
        return self.make_response(
            text,
            buttons=[button('Да', hide=True), button('Нет', hide=True)],
            state={'fallback': self.fallback, 'question_id': question_id},
            card=card
        )

    def handle_local_intents(self, request: Request):
        user = current_user(request)
        user_meant = UserMeaning(request)
        if user_meant.confirm() or user_meant.do_continue():
            gained_level, level, points = user.gained_new_level()
            logging.info(f"Gained level: {gained_level}, LEVEL: {level}, points: {points}")
            print(f"Gained level: {gained_level}, LEVEL: {level}, points: {points}")
            return AskQuestion(give_confirmation=False)
        elif user_meant.deny():
            return Goodbye()
        elif user_meant.repeat():
            return GiveFact(give_confirmation=False)
        return handle_fallbacks(request, GiveFact)


class GetHelp(Main):
    def reply(self, request: Request):
        if self.fallback == 1:
            text = Phrase.give_fallback_general()
        elif self.fallback > 1:
            text = Phrase.give_fallback_2_begin() + ' Пожалуйста, ответь да или нет, -'
        else:
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
                'fallback': self.fallback,
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
                return AskQuestion(lets_play=True)
            else:
                return DifficultyChoice()
        elif user_meant.repeat():
            return GetHelp()
        return handle_fallbacks(request, GetHelp)


class GetVersion(Main):
    def reply(self, request: Request):
        if self.fallback == 1:
            text = Phrase.give_fallback_general()
        elif self.fallback > 1:
            text = Phrase.give_fallback_2_begin() + ' Пожалуйста, ответь да или нет, -'
        else:
            text = f'Версия нейросити {VERSION} . '

        if request.state is not None:
            attempts = search_in_session(request, 'attempts')
            question_id = search_in_session(request, 'question_id')
            clue_given = search_in_session(request, 'clue_given')
            state = {
                'question_id': question_id,
                'clue_given': clue_given,
                'attempts': attempts,
                'fallback': self.fallback,
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
                return AskQuestion(lets_play=True)
            else:
                return DifficultyChoice()
        elif user_meant.repeat():
            return GetVersion()
        return handle_fallbacks(request, GetVersion)


class WhatCanYouDo(Main):
    def reply(self, request: Request):
        if self.fallback == 1:
            text = Phrase.give_fallback_general()
        elif self.fallback > 1:
            text = Phrase.give_fallback_2_begin() + ' Пожалуйста, ответь да или нет, - хочешь сыграть?'
        else:
            text = 'Я нейросеть-гид по Великому Новгороду. ' \
                'Моя база данных повреждена и мне нужна помощь в восстановлении данных. '\
                'Готов ли ты помочь мне?'
        return self.make_response(text, buttons=[
            button('Я готов', hide=True)],
            state={'fallback': self.fallback},
        )
    
    def handle_local_intents(self, request: Request):
        user = current_user(request)
        user_meant = UserMeaning(request)
        user_intent = request.intents
        logging.info(f"{request['session']['session_id']}: User intent - {user_intent}")
        if user_meant.lets_play() or user_meant.confirm():
            if user.difficulty:
                return AskQuestion(lets_play=True)
            else:
                return DifficultyChoice()
        elif user_meant.repeat():
            return WhatCanYouDo()
        return handle_fallbacks(request, WhatCanYouDo)


class GetLevel(Main):
    def reply(self, request: Request):
        if self.fallback == 1:
            text = Phrase.give_fallback_general()
        elif self.fallback > 1:
            text = Phrase.give_fallback_2_begin() + ' Пожалуйста, ответь да или нет, - хочешь сыграть?'
        else:
            user = current_user(request)
            gained_new_level, level, points = user.gained_new_level()
            word = word_in_plural('вопрос', points)
            text = Phrase.get_level() % {'number': points,
                                                 'question': word,
                                                 'level': level}

        return self.make_response(text, buttons=[
            button('Я готов', hide=True)],
            state={'fallback': self.fallback},
        )
    
    def handle_local_intents(self, request: Request):
        user = current_user(request)
        user_meant = UserMeaning(request)
        user_intent = request.intents
        logging.info(f"{request['session']['session_id']}: User intent - {user_intent}")
        if user_meant.lets_play() or user_meant.confirm():
            if user.difficulty:
                return AskQuestion(lets_play=True)
            else:
                return DifficultyChoice()
        elif user_meant.repeat():
            return GetLevel()
        return handle_fallbacks(request, GetLevel)


class Goodbye(Main):
    def reply(self, request: Request):
        if self.fallback == 1:
            text = Phrase.give_fallback_exit()
        elif self.fallback > 1:
            text = Phrase.give_fallback_2_begin()
        else:
            text = 'Буду рад видеть тебя снова!'
        response = self.make_response(text, state={'fallback': self.fallback})
        if 'response' in response.keys():
            response['response']['end_session'] = True
        else:
            response['response'] = {'end_session': True}
        return response

    def handle_local_intents(self, request: Request):
        return handle_fallbacks(request, Goodbye)


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
