import models, random

def test():
    print('\n\n\nTEST\n')
    print('Questions:')
    questions = models.Question.objects.all()
    rand_question = random.choice(list(questions))
    print(rand_question)

    print('\nEND TEST\n\n\n')
