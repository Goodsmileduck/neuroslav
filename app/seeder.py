from models import Phrase, Question, Answer
from pymongo import MongoClient
from settings import DB_HOST, DB_PORT, DB_NAME

CLIENT = MongoClient(DB_HOST, DB_PORT)

def seed_phrases():
    Phrase(1, 'Угадал?').save()
    Phrase(1, 'Именно так.').save()
    Phrase(1, 'Определённо.').save()


def seed_questions():
    Question(
        id=1,
        question_type=1,
        question='В каком году основан Новгород?',
        clue='Очень давно...',
        confirmation_answer='Правильно!!',
        difficulty=3,
        right_answers=[Answer('859')],
        possible_answers=[
            Answer('859'),
            Answer('1859'),
            Answer('1059'),
            Answer('857'),
        ]).save()


def is_db_empty():
    return Phrase.objects.all().count() == 0


def seed_all():
    #drop db before migration
    CLIENT.drop_database(DB_NAME)
    if is_db_empty():
        print('db is empty')
        seed_phrases()
        seed_questions()
