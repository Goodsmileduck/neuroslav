from models import Phrase, Question, RightAnswer, PossibleAnswer


def seed_phrases():
    Phrase(1, 'Угадал?').save()
    Phrase(1, 'Именно так.').save()
    Phrase(1, 'Определённо.').save()


def seed_questions():
    question = Question(question_type=1,
                        question='В каком году основан Новгород?',
                        clue='Очень давно...',
                        confirmation_answer='Правильно!!',
                        difficulty=3)
    question.save()
    RightAnswer(question=question.id,
                answer='859').save()
    PossibleAnswer(question=question.id,
                   answer='859').save()
    PossibleAnswer(question=question.id,
                   answer='1859').save()
    PossibleAnswer(question=question.id,
                   answer='1059').save()
    PossibleAnswer(question=question.id,
                   answer='887').save()


def is_db_empty():
    return Phrase.objects.all().count() == 0


def seed_all():
    if is_db_empty():
        seed_phrases()
        seed_questions()