import unittest
import json
import uuid

import json_const
from alice_emulator import AliceEmulator
# Import modules from parent dir
import sys
sys.path.append('..')
import app

class HandlerTest(unittest.TestCase):
    # Init
    def setUp(self):
        pass
    # Clean up
    def tearDown(self):
        pass
    # Each test method starts with the keyword test_
    def test_welcome(self):
        # TODO fix hack with request string
        user_id = 'test_' + uuid.uuid4().hex
        app_id = 'test_' + uuid.uuid4().hex
        request_str = json_const.first_run
        request_str = request_str.replace('#user_id#', user_id)
        request_str = request_str.replace('#app_id#', app_id)

        request = json.loads(request_str)
        first_response = app.handler(request)
        self.assertTrue(first_response['response']['text'] != '')
        second_response = app.handler(request)
        self.assertTrue(second_response['response']['text'] != '')
        self.assertTrue(second_response['response']['text'] != first_response['response']['text'])

    def test_welcome_alice(self):
        emul = AliceEmulator()
        first_response_text = emul.make_request()
        # self.assertTrue(first_response_text != '')
        second_response_text = emul.make_request()
        # self.assertTrue(second_response_text != '')
        print(first_response_text)
        print(second_response_text)
        self.assertTrue(second_response_text != first_response_text)


if __name__ == "__main__":
    unittest.main()