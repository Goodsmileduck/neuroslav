import models

def test():
    print('test')
    print('Questions:')
    questions = models.Question.objects.all()
    for question in questions:
        print('id:', question.id)

    print('Get Question by id=1')
    questions_ = models.Question.objects.raw({'_id': 1})
    for question in questions_:
        print('id:', question.id)
    print('-')

    print('Get RightAnswers by Question id=1')
    currentQuestion = models.Question.objects.raw({'_id': 1}).first()
    rightAnswers = currentQuestion.right_answers
    for answer in rightAnswers:
        print(answer.answer)

    print('Get RightAnswers (short) by Question id=1')
    rightAnswers_ = models.Question.objects.raw({'_id': 2}).first().right_answers
    for answer in rightAnswers_:
        print(answer.answer)