from models import Phrase, Question, Answer, User, UserQuestion
from pymongo import MongoClient
from settings import DB_HOST, DB_PORT, DB_NAME
import csv, os
from models import PhraseType

CLIENT = MongoClient(DB_HOST, DB_PORT)


def load_csv():
    with open("questions.csv", "r", encoding="utf-8-sig") as csvfile:
        data = csv.DictReader(csvfile, delimiter=";", quotechar='"')
        for q in data:
            print(q['id'])
            right_answers = []
            possible_answers = []
            for x in q["right_answers"].split("|"):
                if x is not None and x != '':
                    right_answers.append(Answer(x.lower()))
            for x in q["possible_answers"].split("|"):
                if x is not None and x != '':
                    possible_answers.append(Answer(x))
            Question(
                id=q["id"],
                question_type=q["question_type"],
                question=q["question"],
                clue=q["clue"],
                difficulty=q["difficulty"],
                right_answers=right_answers,
                interesting_fact=q.get('interesting_fact', ''),
                possible_answers=possible_answers).save()


def seed_phrases():
    Phrase(PhraseType.YOU_ARE_RIGHT.value, 'Угадал!').save()
    Phrase(PhraseType.YOU_ARE_RIGHT.value, 'Именно так. Мои нейроны восстанавливаются!').save()
    Phrase(PhraseType.YOU_ARE_RIGHT.value, 'Определённо верный ответ!').save()
    Phrase(PhraseType.YOU_ARE_RIGHT.value, 'Тысяча нейронов. Это правильно!').save()
    Phrase(PhraseType.YOU_ARE_RIGHT.value, 'Дефрагментировано! Спасибо за верный ответ!').save()
    Phrase(PhraseType.YOU_ARE_RIGHT.value, 'Прекрасный ответ! Так и запишу!').save()
    Phrase(PhraseType.YOU_ARE_RIGHT.value, 'Отлично! Моя база данных наполняется!').save()
    Phrase(PhraseType.YOU_ARE_RIGHT.value, 'Верно, новая нейронная связь создана!').save()
    Phrase(PhraseType.YOU_ARE_RIGHT.value, 'Святые транзисторы, это верно.').save()

    Phrase(PhraseType.YOU_ARE_WRONG.value, 'Не думаю что это верно.').save()
    Phrase(PhraseType.YOU_ARE_WRONG.value, 'Не верно. Я не помню такого.').save()
    Phrase(PhraseType.YOU_ARE_WRONG.value, 'Ответная реакция нейронов не обнаружена. Это неверно.').save()
    Phrase(PhraseType.YOU_ARE_WRONG.value, 'Не припомню такого.').save()
    Phrase(PhraseType.YOU_ARE_WRONG.value, 'Моя память сильно фрагментирована, но это неверный ответ.').save()
    Phrase(PhraseType.YOU_ARE_WRONG.value, 'Не верно. Плохо обученная нейросеть не будет полезной. Нужно обязательно найти ответ.').save()
    Phrase(PhraseType.YOU_ARE_WRONG.value, 'Вероятность этого предельно мала, ответ неверен.').save()
    Phrase(PhraseType.YOU_ARE_WRONG.value, 'Линейное преобразование невозножно, нужен другой ответ.').save()
    Phrase(PhraseType.YOU_ARE_WRONG.value, 'Отсутсвует взаимодействие с другими векторами, значит ответ неверный.').save()
    Phrase(PhraseType.YOU_ARE_WRONG.value, 'Хороший вариант, но не подходит.').save()

    # two %s are necessary! %points and %level :
    Phrase(PhraseType.GREETING.value, 'Привет! Рад видеть тебя снова.\nТы правильно ответил на %(number)i %(question)s и достиг уровня %(level)s!\nСыграем ещё?').save()
    Phrase(PhraseType.GREETING.value, 'Здравствуй! Давно не виделись.\nУ тебя пройдено %(number)i %(question)s! Твой уровень - %(level)s!\nНачнём игру?').save()
    Phrase(PhraseType.GREETING.value, 'Сколько зим! Давно не виделись.\nТы правильно ответил на %(number)i %(question)s и достиг уровня %(level)s!\nИграем?').save()
    Phrase(PhraseType.GREETING.value, 'Рад что снова тут.\nУ тебя пройдено %(number)i %(question)s! Твой уровень - %(level)s!\nИграем?').save()

    Phrase(PhraseType.CONTINUE_ASK.value, 'Продолжим?').save()
    Phrase(PhraseType.CONTINUE_ASK.value, 'Идём дальше?').save()
    Phrase(PhraseType.CONTINUE_ASK.value, 'Продолжаем?').save()
    Phrase(PhraseType.CONTINUE_ASK.value, 'Хочешь продолжить?').save()
    Phrase(PhraseType.CONTINUE_ASK.value, 'Теперь продолжим?').save()

    Phrase(PhraseType.NEXT_QUESTION.value, 'Следующий вопрос.').save()
    Phrase(PhraseType.NEXT_QUESTION.value, 'Перейдём к следующему вопросу.').save()
    Phrase(PhraseType.NEXT_QUESTION.value, 'Я нашел еще фрагмент памяти.').save()
    Phrase(PhraseType.NEXT_QUESTION.value, 'А вот и еще вопрос.').save()
    Phrase(PhraseType.NEXT_QUESTION.value, 'Переходим в следующий слой нейросети. Нашел вопрос.').save()
    Phrase(PhraseType.NEXT_QUESTION.value, 'Где-то тут потерялся нейрон. Значит вот тебе вопрос.').save()
    Phrase(PhraseType.NEXT_QUESTION.value, 'Итак, новый вопрос.').save()
    Phrase(PhraseType.NEXT_QUESTION.value, 'Новый вопрос звучит так: ').save()

    Phrase(PhraseType.OFFER_CLUE.value, 'Дать подсказку?').save()
    Phrase(PhraseType.OFFER_CLUE.value, 'Хочешь подсказку?').save()

    # two %s are necessary! %points and %level :
    Phrase(PhraseType.NEW_LEVEL_CONGRATULATION.value, 'Поздравляю, ты правильно ответил на %(number)i %(question)s и достиг уровня %(level)s! Продолжай в том же духе!\nСледующий вопрос?').save()
    Phrase(PhraseType.NEW_LEVEL_CONGRATULATION.value, 'Невероятно, у тебя пройдено %(number)i %(question)! Твой новый уровень - %(level)s!\nИдём дальше?').save()

    Phrase(PhraseType.TRY_AGAIN.value, 'Попробуй ещё раз.').save()
    Phrase(PhraseType.TRY_AGAIN.value, 'Попытайся снова.').save()
    Phrase(PhraseType.TRY_AGAIN.value, 'Нужно попробовать еще.').save()
    Phrase(PhraseType.TRY_AGAIN.value, 'Давай еще попытку.').save()
    Phrase(PhraseType.TRY_AGAIN.value, 'Надо попробовать еще.').save()


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
