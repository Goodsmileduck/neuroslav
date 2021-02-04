import unittest
import json
import uuid

import json_const
from alice_emulator import AliceEmulator
# Import modules from parent dir
import sys
sys.path.append('..')
import app
import scenes
import models
import handlers


class HandlerTest(unittest.TestCase):
    handler = None
    # Init
    def setUp(self):
        self.handler = handlers.HandleAppRequest()
        # self.handler = handlers.HandleWebRequest('https://neuroslav.prod.kubeapp.ru') # production
        # self.handler = handlers.HandleWebRequest('https://neuroslav-jx-staging.kubeapp.ru') #staging
        # self.handler = handlers.HandleWebRequest('https://c6f5bb40e06f.ngrok.io')  # dev
        pass
    # Clean up
    def tearDown(self):
        pass
    # Each test method starts with the keyword test_
    # def test_welcome(self):
    #     # TODO fix hack with request string
    #     user_id = 'test_' + uuid.uuid4().hex
    #     app_id = 'test_' + uuid.uuid4().hex
    #     request_str = json_const.first_run
    #     request_str = request_str.replace('#user_id#', user_id)
    #     request_str = request_str.replace('#app_id#', app_id)
    #
    #     request = json.loads(request_str)
    #     first_response = app.handler(request)
    #     self.assertTrue(first_response['response']['text'] != '')
    #     second_response = app.handler(request)
    #     self.assertTrue(second_response['response']['text'] != '')
    #     self.assertTrue(second_response['response']['text'] != first_response['response']['text'])

    def test_emulator(self):
        alice = AliceEmulator(self.handler)
        alice.make_request()
        self.assertEqual(alice.response_state['scene'], alice.request_state['scene'], 'Scenes must be equal')

    def test_welcome(self):
        alice = AliceEmulator(self.handler)

        # Make first request
        first_response_text = alice.make_request()
        self.assertTrue(first_response_text != '', 'Welcome message (first run) can not be empty')
        self.assertEqual(alice.request_state['scene'], 'Welcome', 'Scene must be Welcome')

        # Make second request
        second_response_text = alice.make_request()
        self.assertTrue(second_response_text != 'Welcome message (second run) can not be empty')
        # TODO Uncomment line
        # self.assertTrue(second_response_text != first_response_text, 'Welcome message (first run) must be not equal to Welcome message (second run)')

    def test_case02(self):
        alice = AliceEmulator(self.handler)

        alice.make_request()
        self.assertEqual(alice.response_state['scene'], 'Welcome', 'Scene must be Welcome')

        alice.set_text('давай играть')
        response_text = alice.make_request()
        self.assertNotEqual(response_text, '', 'Response text must not be empty')
        self.assertEqual(alice.response_state['scene'], 'DifficultyChoice', 'Scene must be DifficultyChoice')

        alice.set_text('простой')
        response_text = alice.make_request()
        question_id_1 = alice.response_state['question_id']
        question = models.Question.objects.get({'_id': question_id_1})
        self.assertIn(question.question, response_text, 'Question text must be equal to stored question_id')
        user = scenes.current_user(alice.request)
        self.assertNotEqual(user, None, 'User must be stored in db')
        self.assertEqual(user.points(), 0, 'New user must be without points')
        self.assertEqual(user.difficulty, 1, 'User difficulty must be 1 (easy)')
        self.assertEqual(alice.response_state['scene'], 'AskQuestion', 'Scene must be AskQuestion')
        self.assertEqual(alice.response_state['clue_given'], False, 'clue_given must be False')

        alice.set_text('помоги')
        response_text = alice.make_request()
        self.assertNotEqual(response_text, '', 'Response text must not be empty')
        question_id_2 = alice.response_state['question_id']
        question = models.Question.objects.get({'_id': question_id_2})
        self.assertEqual(question_id_1, question_id_2, 'Question must not be changed')
        self.assertIn(question.clue, response_text, 'Question clue must be equal to stored question_id')
        self.assertEqual(alice.response_state['scene'], 'AskQuestion', 'Scene must be AskQuestion')
        self.assertEqual(alice.response_state['clue_given'], True, 'clue_given must be True')

    def test_case07(self):
        alice = AliceEmulator(self.handler)

        alice.make_request()
        self.assertEqual(alice.response_state['scene'], 'Welcome', 'Scene must be Welcome')

        alice.set_text('давай играть')
        response_text = alice.make_request()
        self.assertNotEqual(response_text, '', 'Response text must not be empty')
        self.assertEqual(alice.response_state['scene'], 'DifficultyChoice', 'Scene must be DifficultyChoice')

        alice.set_text('трудный')
        alice.make_request()
        user = scenes.current_user(alice.request)
        self.assertNotEqual(user, None, 'User must be stored in db')
        self.assertEqual(user.difficulty, 2, 'User difficulty must be 2 (hard)')
        self.assertEqual(alice.response_state['scene'], 'AskQuestion', 'Scene must be AskQuestion')
        self.assertEqual(alice.response_state['clue_given'], False, 'clue_given must be False')
        question_id = alice.response_state['question_id']

        alice.set_text('не знаю')
        response_text = alice.make_request()
        self.assertNotEqual(response_text, '', 'Response text must not be empty')
        phrases = [p.phrase for p in list(models.Phrase.objects.raw({'phrase_type': models.PhraseType.OFFER_CLUE.value}))]
        self.assertIn(response_text, phrases, 'Phrase must be in OFFER_CLUE list')

        alice.set_text('давай')
        response_text = alice.make_request()
        question_id_ = alice.response_state['question_id']
        question = models.Question.objects.get({'_id': question_id_})
        self.assertEqual(question_id, question_id_, 'Question must not be changed')
        self.assertIn(question.clue, response_text, 'Question clue must be equal to stored question_id')
        self.assertEqual(alice.response_state['scene'], 'AskQuestion', 'Scene must be AskQuestion')
        self.assertEqual(alice.response_state['clue_given'], True, 'clue_given must be True')

    def test_case09(self):
        # Init scene
        alice = AliceEmulator(self.handler)

        alice.make_request()
        self.assertEqual(alice.response_state['scene'], 'Welcome', 'Scene must be Welcome')

        alice.set_text('давай играть')
        response_text = alice.make_request()
        self.assertNotEqual(response_text, '', 'Response text must not be empty')
        self.assertEqual(alice.response_state['scene'], 'DifficultyChoice', 'Scene must be DifficultyChoice')

        alice.set_text('легкий')
        response_text = alice.make_request()
        self.assertEqual(alice.response_state['scene'], 'AskQuestion', 'Scene must be AskQuestion')

        # Some preparations
        phrases = [p.phrase for p in
                   list(models.Phrase.objects.raw({'phrase_type': models.PhraseType.YOU_ARE_RIGHT.value}))]

        user = scenes.current_user(alice.request)
        self.assertNotEqual(user, None, 'User must be stored in db')
        is_running = True
        max_iterations = 4
        i = 1
        question = None

        while is_running:
            # Check fact
            if alice.response_state['scene'] == 'GiveFact':
                self.assertIn(question.interesting_fact, response_text, 'Incorrect fact given')
                self.assertLess(user.points(), 3, 'LevelCongratulation must be shown instead of GiveFact')
                alice.set_text('да')
                response_text = alice.make_request()
            # Our goal
            if alice.response_state['scene'] == 'LevelCongratulation':
                break
            if i >= max_iterations:
                self.assertTrue(False, 'Max iterations reached')

            # Current question
            self.assertEqual(alice.response_state['scene'], 'AskQuestion', 'Scene must be AskQuestion')
            question_id = alice.response_state['question_id']
            question = models.Question.objects.get({'_id': question_id})
            # Send right answer
            alice.set_text(question.right_answers[0].answer)
            response_text = alice.make_request()
            self.assertEqual(user.points(), i, 'User has invalid points')
            # Check phrases for Right answer
            if alice.response_state['scene'] != 'LevelCongratulation':
                is_phrase_found = False
                for phrase in phrases:
                    if phrase in response_text:
                        is_phrase_found = True
                        break
                self.assertTrue(is_phrase_found, 'Response text must contains YOU_ARE_RIGHT phrase')
            i += 1

    def test_difficulties(self):
        difficulties = [
            {'text': 'легкий', 'value': 1},
            {'text': 'давай легкий', 'value': 1},
            {'text': 'выбираю легкий', 'value': 1},
            {'text': 'хочу легкий', 'value': 1},
            {'text': 'простой', 'value': 1},
            {'text': 'давай простой', 'value': 1},
            {'text': 'хочу простой', 'value': 1},
            {'text': 'трудный', 'value': 2},
            {'text': 'давай трудный', 'value': 2},
            {'text': 'хочу трудный', 'value': 2},
            {'text': 'выбираю трудный', 'value': 2},
            {'text': 'сложный', 'value': 2},
        ]

        for difficulty in difficulties:
            alice = AliceEmulator(self.handler)
            alice.make_request()
            self.assertEqual(alice.response_state['scene'], 'Welcome', 'Scene must be Welcome')
            alice.set_text('давай играть')
            alice.make_request()
            self.assertEqual(alice.response_state['scene'], 'DifficultyChoice', 'Scene must be DifficultyChoice')
            alice.set_text(difficulty['text'])
            alice.make_request()
            user = scenes.current_user(alice.request)
            self.assertNotEqual(user, None, 'User must be stored in db')
            self.assertEqual(user.difficulty, difficulty['value'], 'User difficulty is wrong')

        # TODO Add negative tests

    def test_lets_play(self):
        phrases = [
            {'text': 'давай играть'},
            {'text': 'начнем'},
            {'text': 'играем'},
            {'text': 'сыграем'},
            {'text': 'поехали'},
            {'text': 'могу'},
        ]

        for phrase in phrases:
            alice = AliceEmulator(self.handler)
            alice.make_request()
            self.assertEqual(alice.response_state['scene'], 'Welcome', 'Scene must be Welcome')
            alice.set_text(phrase['text'])
            alice.make_request()
            self.assertEqual(alice.response_state['scene'], 'DifficultyChoice', 'Scene must be DifficultyChoice')

        # TODO Add negative tests

    def test_case02_several_times(self):
        for i in range(1, 100):
            self.test_case02()

    def test_case07_several_times(self):
        for i in range(1, 100):
            self.test_case07()

    def test_case09_several_times(self):
        for i in range(1, 100):
            self.test_case09()


if __name__ == "__main__":
    unittest.main()