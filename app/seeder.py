from models import Phrase, Question, Answer, User, UserQuestion
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
            for x in q["right_answers"].split("|"):
                if x is not None and x is not '':
                    right_answers.append(Answer(x.lower()))
            for x in q["possible_answers"].split("|"):
                if x is not None and x is not '':
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
    Phrase(1, 'Именно так. Мои нейроны восстанавливаются!').save()
    Phrase(1, 'Определённо верный ответ!').save()
    Phrase(1, 'Тысяча нейронов. Это правильно!').save()

    Phrase(2, 'Не думаю что это верно.').save()
    Phrase(2, 'Не верно. Я не помню такого.').save()
    Phrase(2, 'Ответная реакция нейронов не обнаружена. Попробуй еще раз.').save()
    Phrase(2, 'Не припомню такого.').save()

    Phrase(4, 'Привет! Рад видеть тебя снова. Сыграем?').save()
    Phrase(4, 'Здравствуй! Давно не виделись. Начнём игру?').save()

    Phrase(5, 'Продолжим?').save()
    Phrase(5, 'Идём дальше?').save()

    Phrase(6, 'Следующий вопрос.').save()
    Phrase(6, 'Перейдём к следующему вопросу.').save()

    Phrase(7, 'Поздравляю, ты достиг уровня %s! Продолжай в том же духе!\nСледующий вопрос?').save()
    Phrase(7, 'Невероятно! У тебя новый уровень - %s!\nИдём дальше?').save()

    Phrase(8, 'Попробуй ещё раз.').save()
    Phrase(8, 'Попытайся снова.').save()



def seed_questions():
    load_csv()

def test_seed():
    pass
    # user = User(application_id='1230-412').save()
    # question = Question.objects.all().first()
    # user_question = UserQuestion(user=user, question=question, passed=True).save()
    # print(user_question, user_question.user)
    # print(UserQuestion.objects.all().first())


def is_db_empty():
    return Phrase.objects.all().count() == 0


def seed_all():
    # drop db before migration
    CLIENT.drop_database(DB_NAME)
    if is_db_empty():
        print('db is empty')
        seed_phrases()
        seed_questions()
        test_seed()
