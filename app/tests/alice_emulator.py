import json
import uuid

import json_const
# Import modules from parent dir
import sys
sys.path.append('..')
import app

class AliceEmulator:
    request = None
    response = None

    def __init__(self):
        self.load_empty_request()
        self.generate_new_user()
        pass

    def load_empty_request(self):
        self.request = json.loads(json_const.first_run)

    def set_user(self, u_id, app_id):
        self.request['session']['user']['user_id'] = u_id
        self.request['session']['application']['application_id'] = app_id
        self.request['session']['user_id'] = app_id
        pass

    def generate_new_user(self):
        user_id = 'test_' + uuid.uuid4().hex
        app_id = 'test_' + uuid.uuid4().hex
        self.set_user(user_id, app_id)

    def set_text(self, text, original_utterance = ''):
        self.request['request']['command'] = text
        if original_utterance == '':
            original_utterance = text
        self.request['request']['original_utterance'] = original_utterance

    def make_request(self):
        self.response = app.handler(self.request)
        return self.response['response']['text']

    def update_state(self):
        self.request['state']['session'] = self.response['response']['state']
