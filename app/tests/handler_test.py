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

class HandlerTest(unittest.TestCase):
    # Init
    def setUp(self):
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
        alice = AliceEmulator()
        alice.make_request()
        self.assertEqual(alice.response_state['scene'], alice.request_state['scene'], 'Scenes must be equal')

    def test_welcome(self):
        alice = AliceEmulator()

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
        alice = AliceEmulator()

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
        self.assertEqual(alice.response_state['clue_given'], True, 'clue_given must be False')


if __name__ == "__main__":
    unittest.main()