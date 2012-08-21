
import platform
from webob import Request, Response

class InterceptorMiddleware(object):
    
    def __init__(self, app, config):
        self.app = app
        self.config = config

    def __call__(self, environ, start_response):
        #def local_response(status, headers):
        #    headers += [('X-Server-Machine', platform.node())]
        #    start_response(status, headers)
        req = Request(environ)
        rsp = req.get_response(self.app)
        rsp.headers['X-Server-Machine'] = platform.node()
        return rsp(environ, start_response)
        #return self.app(environ, start_response)
