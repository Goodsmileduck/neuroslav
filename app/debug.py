import models

def test():
    print('test')
    print('Questions:')
    questions = models.Question.objects.all()
    for question in questions:
        print('id:', question.id)

    print('Get Question by id=1')
    questions_ = models.Question.objects.raw({'id': 1})
    for question in questions_:
        print('id:', question.id)
    print('-')