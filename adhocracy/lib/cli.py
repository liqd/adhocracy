import itertools
import os

import paste.script
import paste.fixture
import paste.registry
import paste.deploy.config
from paste.deploy import loadapp
from paste.script.command import Command

from adhocracy import model
from adhocracy.lib import search


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
        self.setup_timer(86400.0, self.daily)

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
    """Re-create Adhocracy's search index."""
    summary = __doc__.split('\n')[0]
    max_args = 999
    min_args = None

    DROP = 'DROP'
    INDEX = 'INDEX'

    errors = False
    _indexed_classes = None

    def get_instances(self, args):

        names = []
        INSTANCES_KEYWORD = '-I'
        remaining_args = args[:]
        if INSTANCES_KEYWORD in args:
            index = args.index(INSTANCES_KEYWORD)
            names = self.args[index + 1:]
            remaining_args = args[:index]

        instances = []
        for name in names:
            instance = model.Instance.find(name, include_deleted=True)
            if not instance:
                print 'Instance "%s" not found.\n' % name
                self.errors = True
            else:
                instances.append(instance)
        return (remaining_args, instances)

    def get_classes(self, args):
        classes = []
        for name in args:
            cls = self.indexed_classes.get(name)
            if cls is None:
                print 'Unknown content type "%s"' % name
                self.errors = True
            else:
                classes.append(cls)
        return classes

    def get_actions(self, args):
        actions = []
        for action in [self.DROP, self.INDEX]:
            if action in args:
                actions.append(action)
                args.remove(action)
        if not actions:
            print 'No actions specified.'
            self.errors = True
        return args, actions

    def command(self):
        self._load_config()

        # b/w compatibity
        if not self.args:
            self.start([self.INDEX], [], [])
            exit(0)

        args = self.args[:]

        args, instances = self.get_instances(args)
        args, actions = self.get_actions(args)
        classes = self.get_classes(args)

        if self.errors:
            exit(1)
        else:
            self.start(actions, classes, instances)

    def printable(self, items, print_=lambda x: x):
        if not items:
            return 'ALL'
        else:
            return ', '.join([print_(item) for item in items])

    def start(self, actions, classes, instances):
        print ('Starting.\n'
               '  Actions: %s\n'
               '  Content Types: %s\n'
               '  Instances: %s\n') % (
                   self.printable(actions),
                   self.printable(classes,
                                  print_=lambda x: x.__name__.lower()),
                   self.printable(instances, print_=lambda x: x.key))

        if self.DROP in actions:
            p_instances = instances if instances else [None]
            p_classes = classes if classes else [None]

            print 'Dropping docs from solr... '
            for (cls, instance) in itertools.product(p_classes, p_instances):
                print 'content_type: %s, instance: %s' % (cls, instance)
                search.drop(cls, instance)
            print '...done.'

        if self.INDEX in actions:
            classes = classes if classes else self.indexed_classes.values()
            search.rebuild(classes, instances=instances)
            print 'done.'
            return

    @property
    def indexed_classes(self):
        if self._indexed_classes is None:
            self._indexed_classes = dict([(cls.__name__.lower(), cls) for
                                          cls in search.INDEXED_CLASSES])
        return self._indexed_classes

    @property
    def usage(self):
        usage = self.__doc__ + '\n\n'
        indexed_classes = sorted(self.indexed_classes.keys())
        content_types = '\n          '.join(indexed_classes)
        usage += (
            'index (ALL|DROP) [<entity>, ...] [-I <instance>, ...]'
            ' -c <inifile>'
            '\n\n'
            '  DROP_ALL:\n'
            '      Remove all documents from solr.\n'
            '  ALL\n'
            '      Index all content in solr.\n'
            '      Default if no arguments are given\n'
            '  <entity>\n'
            '      Names of a content types to index. If not given,\n'
            '      all content is indexed. Types:\n'
            '          %s\n'
            '  -I <instance>, ...\n'
            '      Reindex only content from the instances. Note: Users\n'
            '      are dropped if they are member in one of the instances,\n'
            '      even if they are also member in other instances.'
        ) % content_types

        return usage
