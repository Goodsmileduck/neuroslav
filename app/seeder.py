from models import Phrase, Question, Answer


def seed_phrases():
    Phrase(1, 'Угадал?').save()
    Phrase(1, 'Именно так.').save()
    Phrase(1, 'Определённо.').save()


def seed_questions():
    Question(question_type=1,
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
    if is_db_empty():
        seed_phrases()
        seed_questions()