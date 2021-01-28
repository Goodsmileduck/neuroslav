from models import Phrase, Question, Answer
from pymongo import MongoClient
from settings import DB_HOST, DB_PORT, DB_NAME

CLIENT = MongoClient(DB_HOST, DB_PORT)

def seed_phrases():
    Phrase(1, 'Угадал!').save()
    Phrase(1, 'Именно так.').save()
    Phrase(1, 'Определённо.').save()

    Phrase(2, 'Не угадал.').save()
    Phrase(2, 'Не верно.').save()
    Phrase(2, 'Реакция нейронов не обнаружена.').save()


def seed_questions():
    Question(
        id=1,
        question_type=1,
        question='В каком году основан Новгород?',
        clue='Очень давно...',
        confirmation_answer='Правильно!!',
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
        question='Зачем это всё?',
        clue='Подсказка..',
        confirmation_answer='Верно!!',
        difficulty=2,
        right_answers=[Answer('да')],
        interesting_fact='Просто интересный факт',
        possible_answers=[
            Answer('Да'),
            Answer('Нет'),
        ]).save()

    Question(
        id=3,
        question_type=1,
        question='Как называется главный новгородский храм?',
        clue='Со...',
        confirmation_answer='Именно!',
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
        confirmation_answer='Именно!',
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
