import itertools
from logging import getLogger
import os
import signal
import threading
import time

import paste.script
import paste.fixture
import paste.registry
import paste.deploy.config
from paste.deploy import loadapp
from paste.script.command import Command
import rq

from adhocracy import model
from adhocracy.lib import search
from adhocracy.lib import queue


log = getLogger(__name__)


class AdhocracyCommand(Command):
    parser = Command.standard_parser(verbose=True)
    parser.add_option('-c', '--config', dest='config',
            default='etc/adhocracy.ini', help='Config file to use.')
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


class AdhocracyTimer(object):

    timer_duration = 60

    periodicals = {
        'minutely': dict(delay=60.0, task=queue.minutely),
        'hourly': dict(delay=3600.0, task=queue.hourly),
        'daily': dict(delay=86400.0, task=queue.daily)}

    def __init__(self, redis, queue_name):
        self.redis = redis
        self.queue_name = queue_name

    @property
    def lock_key(self):
        return '%s.guard.lock' % self.queue_name

    @property
    def schedules_key(self):
        return '%s.shedules' % self.queue_name

    def guard(self):
        '''
        check if any of our peridical functions has to be called.
        This will set up a timer to call itself every 60 seconds.
        '''
        if self.get_lock():
            self.run_periodicals()
        self.setup_timer(self.timer_duration, self.guard)

    def run_periodicals(self):
        '''
        Run the periodical functions and do schedule the next
        execution times if necessary.
        '''
        hash_name = self.schedules_key
        now = time.time()
        for key_name, periodical in self.periodicals.items():
            log.debug('periodical: %s' % str(periodical))
            self.redis.hsetnx(hash_name, key_name, 0)
            next_run = self.redis.hget(hash_name, key_name)
            log.debug('next_run: %s' % next_run)
            if float(next_run) < (now + 1):
                log.debug('run now.')
                periodical['task'].enqueue()
                next_run = float(now + periodical['delay'])
                self.redis.hset(hash_name, key_name, next_run)

        # expire our schedules hash an our after the next sheduled run
        max_duration = max([p['delay'] for p in self.periodicals.values()])
        expire = max_duration + 3600
        self.redis.expire(hash_name, int(expire))

    def get_lock(self):
        '''
        Return `True` if we have or can set a lock in redis. The lock
        will be set or extended for the given *duration* from (from
        the time it is set or renewed) and is valid for the current
        process.
        '''
        redis = self.redis
        key = self.lock_key
        duration = self.timer_duration + 1
        pid = self.pid

        log.debug('get_lock, pid: %s...' % pid)
        # set a new lock if it does not exist
        if redis.setnx(key, pid):
            redis.expire(key, duration)
            log.debug('new')
            return True

        # Get the current lock and check if it is ours:
        current_value = redis.get(key)
        log.debug('current value: %s, type: %s' % (current_value,
                                                   type(current_value)))
        if int(current_value) == pid:
            redis.expire(key, duration)
            #log.debug('extended')
            return True

        log.debug('nope')
        return False

    def setup_timer(self, interval, func):
        timer = threading.Timer(interval, func)
        timer.daemon = True
        timer.start()

    def start(self):
        self.pid = os.getpid()
        self.guard()


class Timer(AdhocracyCommand):
    '''
    Schedule periodical jobs.
    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = None
    min_args = None

    def command(self):
        self._load_config()
        redis = queue.rq_config.connection
        if not redis:
            log.error('No redis connection available')
            exit(1)
        self.timer = AdhocracyTimer(redis, queue.rq_config.queue_name)
        self.timer.start()  # this will setup a timer thread
        signal.signal(signal.SIGTERM, lambda signum, frame: exit(0))
        signal.signal(signal.SIGINT, lambda signum, frame: exit(0))
        signal.pause()


class Worker(AdhocracyCommand):
    '''Run Adhocracy background jobs.'''
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = None
    min_args = None

    redis = None
    queue = None

    def command(self):
        self._load_config()
        queue.rq_config.in_worker = True
        connection = queue.rq_config.connection
        if not connection:
            log.error('No redis connection available')
            exit(1)
        queue_ = queue.rq_config.queue
        if not queue_:
            log.error('No queue available.')
            exit(1)
        worker = rq.Worker([queue_], connection=connection)
        worker.work()


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
            'index (INDEX|DROP|DROP_ALL|ALL) [<entity>, ...] [-I <instance>, ...]'
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
