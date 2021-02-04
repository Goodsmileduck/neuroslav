import json
import uuid

import json_const
# Import modules from parent dir
import sys
sys.path.append('..')
import app
from state import STATE_RESPONSE_KEY, STATE_REQUEST_KEY
import handlers

class AliceEmulator:
    request = None
    response = None
    handler = None

    def __init__(self, handler = None):
        self.load_empty_request()
        self.generate_new_user()
        if not handler:
            handler = handlers.HandleAppRequest()
        self.handler = handler
        pass

    def load_empty_request(self):
        self.request = json.loads(json_const.first_run)

    def set_user(self, u_id, app_id):
        # TODO Move to properties
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

    def make_request(self, auto_update_state = True):
        self.response = self.handler.handle(self.request)
        if auto_update_state:
            self.update_state()
        return self.response_text


    @property
    def request_state(self):
        return self.request['state'][STATE_REQUEST_KEY]

    @request_state.setter
    def request_state(self, value):
        self.request['state'][STATE_REQUEST_KEY] = value


    @property
    def response_state(self):
        return self.response[STATE_RESPONSE_KEY]

    @response_state.setter
    def response_state(self, value):
        self.response[STATE_RESPONSE_KEY] = value


    @property
    def response_text(self):
        return self.response['response']['text']


    def update_state(self):
        self.request_state = self.response_state
