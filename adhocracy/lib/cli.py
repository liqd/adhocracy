import os

import paste.script
import paste.fixture
import paste.registry
import paste.deploy.config
from paste.deploy import loadapp
from paste.script.command import Command


class AdhocracyCommand(Command):
    parser = Command.standard_parser(verbose=True)
    parser.add_option('-c', '--config', dest='config',
            default='development.ini', help='Config file to use.')
    default_verbosity = 1
    group_name = 'adhocracy'

    def _load_config(self):
        from paste.deploy import appconfig
        if not self.options.config:
            msg = 'No config file supplied'
            raise self.BadCommand(msg)
        self.filename = os.path.abspath(self.options.config)
        self.logging_file_config(self.filename)
        conf = appconfig('config:' + self.filename)
        conf.update(dict(app_conf=conf.local_conf,
                         global_conf=conf.global_conf))
        paste.deploy.config.CONFIG.push_thread_config(conf)
        wsgiapp = loadapp('config:' + self.filename)
        test_app = paste.fixture.TestApp(wsgiapp)
        tresponse = test_app.get('/_test_vars')
        request_id = int(tresponse.body)
        test_app.pre_request_hook = lambda self: \
            paste.registry.restorer.restoration_end()
        test_app.post_request_hook = lambda self: \
            paste.registry.restorer.restoration_begin(request_id)
        paste.registry.restorer.restoration_begin(request_id)

    def _setup_app(self):
        cmd = paste.script.appinstall.SetupCommand('setup-app')
        cmd.run([self.filename])


class Background(AdhocracyCommand):
    '''Run Adhocracy background jobs.'''
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = None
    min_args = None

    def minute(self):
        import adhocracy.lib.queue as queue
        queue.minute()
        self.setup_timer(60.0, self.minute)

    def hourly(self):
        import adhocracy.lib.queue as queue
        queue.hourly()
        self.setup_timer(3600.0, self.hourly)

    def daily(self):
        import adhocracy.lib.queue as queue
        queue.daily()
        self.setup_timer(84600.0, self.daily)

    def setup_timer(self, interval, func):
        import threading
        timer = threading.Timer(interval, func)
        timer.daemon = True
        timer.start()

    def command(self):
        self._load_config()
        self.minute()
        self.hourly()
        self.daily()
        import queue
        queue.dispatch()


class Index(AdhocracyCommand):
    '''Re-create Adhocracy's search index.'''
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = None
    min_args = None

    def command(self):
        self._load_config()
        import search
        search.rebuild_all()
