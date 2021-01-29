from models import Phrase, Question, Answer
from pymongo import MongoClient
from settings import DB_HOST, DB_PORT, DB_NAME
import csv, os

CLIENT = MongoClient(DB_HOST, DB_PORT)


def load_csv():

    with open("questions.csv", "r", encoding="utf-8-sig") as csvfile:
        data = csv.DictReader(csvfile, delimiter=";", quotechar='"')
        for q in data:
            print(q['id'])
            right_answers = []
            possible_answers = []
            for x in q["right_answers"]:
                right_answers.append(Answer(x))
            for x in q["possible_answers"]:
                possible_answers.append(Answer(x))
            Question(
                id=q["id"],
                question_type=q["question_type"],
                question=q["question"],
                clue=q["clue"],
                difficulty=q["difficulty"],
                right_answers=right_answers,
                interesting_fact=None,
                possible_answers=possible_answers).save()


def seed_phrases():
    Phrase(1, 'Угадал!').save()
    Phrase(1, 'Именно так.').save()
    Phrase(1, 'Определённо.').save()
    Phrase(1, 'Тысяча нейронов! Это правильно.').save()

    Phrase(2, 'Не думаю что это верно.').save()
    Phrase(2, 'Не верно. Я не помню такого.').save()
    Phrase(2, 'Ответная реакция нейронов не обнаружена.').save()

    Phrase(4, 'Привет! Рад видеть тебя снова. Сыграем?').save()
    Phrase(4, 'Здравствуй! Давно не виделись. Начнём игру?').save()

    Phrase(5, 'Продолжим?').save()
    Phrase(5, 'Идём дальше?').save()


def seed_questions():
    Question(
        id=1,
        question_type=1,
        question='В каком году основан Новгород?',
        clue='Очень давно...',
        difficulty=3,
        right_answers=[Answer('859')],
        interesting_fact='Интересный факт о Новгороде',
        possible_answers=[
            Answer('859'),
            Answer('1859'),
            Answer('1059'),
            Answer('857'),
        ]).save()

    Question(
        id=2,
        question_type=2,
        question='Верно?',
        clue='Что тут думать?',
        difficulty=2,
        right_answers=[Answer('верно')],
        interesting_fact='Просто интересный факт',
        possible_answers=[
            Answer('верно'),
            Answer('не верно'),
        ]).save()

    Question(
        id=3,
        question_type=1,
        question='Как называется главный новгородский храм?',
        clue='Со...',
        difficulty=3,
        right_answers=[
            Answer('софийский собор'),
            Answer('собор софии'),
            Answer('собор святой софии'),
            Answer('святой софии'),
        ],
        interesting_fact='Интересный факт о Соборе Святой Софии',
        possible_answers=[
            Answer('Собор Святой Софии'),
            Answer('Храм Христа Спасителя'),
            Answer('Церковь Богородицы'),
            Answer('Новгородский Собор'),
        ]).save()

    Question(
        id=4,
        question_type=2,
        question='Подвергался ли Новгород монгольскому нашествию?',
        clue='Может быть',
        difficulty=3,
        right_answers=[
            Answer('нет'),
        ],
        interesting_fact='Батый не дошёл до города 200 км, и хоть Новгород платил дань Орде, но сохранил уникальные памятники древнерусской архитектуры и был единственным из древних русских городов, избежавшим упадка.',
        possible_answers=[
            Answer('Да'),
            Answer('Нет'),
        ]).save()


def is_db_empty():
    return Phrase.objects.all().count() == 0


def seed_all():
    # drop db before migration
    CLIENT.drop_database(DB_NAME)
    if is_db_empty():
        print('db is empty')
        seed_phrases()
        seed_questions()
