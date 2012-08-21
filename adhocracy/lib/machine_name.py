
import platform
from webob import Request, Response

class IncludeMachineName(object):
    
    def __init__(self, app, config):
        self.app = app
        self.config = config

    def __call__(self, environ, start_response):
        req = Request(environ)
        rsp = req.get_response(self.app)
        rsp.headers['X-Server-Machine'] = platform.node()
        return rsp(environ, start_response)
