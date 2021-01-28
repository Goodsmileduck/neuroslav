from models import Phrase

def seed_phrases():
    Phrase(1, 'Угадал?').save()
    Phrase(1, 'Именно так.').save()
    Phrase(1, 'Определённо.').save()

def seed_all():
    seed_phrases()