from abc import ABC, abstractmethod
import app
import requests

# import urllib3
# import json


class BaseHandler(ABC):
    @abstractmethod
    def handle(self, request):
        raise NotImplementedError()


class HandleAppRequest(BaseHandler):
    def handle(self, request):
        return app.handler(request)


class HandleWebRequest(BaseHandler):
    url = ''

    def __init__(self, url):
        self.url = url

    def handle(self, request):
        session = requests.Session()
        session.keep_alive = False
        response = requests.post(
            self.url,
            data = None,
            json = request,
            stream  = False,
            timeout=3,
        )
        jsonResponse = response.json()
        #response = None
        session.close()
        return jsonResponse

    # def handle(self, request):
    #     with urllib3.PoolManager(num_pools=50) as conn:
    #         encoded_request = json.dumps(request).encode('utf-8')
    #         r = conn.request(
    #             'POST',
    #             self.url,
    #             body = encoded_request,
    #             headers={'Content-Type': 'application/json'},
    #             timeout=urllib3.Timeout(connect=1.0, read=2.0)
    #         )
    #         jsonResponse = json.loads(r.data.decode('utf-8'))
    #         return jsonResponse