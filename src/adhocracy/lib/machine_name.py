
import os
import platform


class IncludeMachineName(object):

    def __init__(self, app, config):
        self.app = app
        self.config = config

    def __call__(self, environ, start_response):
        def local_response(status, headers, exc_info=None):
            machine_id = '%s:%s (PID %d)' % (
                platform.node(), environ.get('SERVER_PORT'), os.getpid())
            headers.append(('X-Server-Machine', machine_id))
            start_response(status, headers, exc_info)
        return self.app(environ, local_response)
