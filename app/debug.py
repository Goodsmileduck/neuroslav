import models, random
from scenes import random_phrase

def test():
    print('\n\n\nTEST\n')
    user = models.User(application_id='A9A8E1CB150550B27DEECBD766B436D6B098C96E9768BFE7F9C58A96DB437886', difficulty=1).save()
    print('=============', models.PhraseType.OFFER_CLUE)
    print('=============', models.PhraseType.OFFER_CLUE.value)
    print(random_phrase(models.PhraseType.OFFER_CLUE))
    print(random_phrase(models.PhraseType.OFFER_CLUE.value))

    print('\nEND TEST\n\n\n')
