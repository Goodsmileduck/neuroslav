import models, random


def test():
    print('\n\n\nTEST\n')
    user = models.User(application_id='A9A8E1CB150550B27DEECBD766B436D6B098C96E9768BFE7F9C58A96DB437886', difficulty=2).save()
    for question in models.Question.objects.all():
        models.UserQuestion(user=user._id, question=question.id, passed=True).save()

    print(user.gained_new_level())

    print(models.Phrase.give_you_are_right())

    print('\nEND TEST\n\n\n')
