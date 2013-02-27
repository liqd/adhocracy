from collections import defaultdict
import json
from logging import getLogger

from redis import Redis
from rq import Queue
from rq.job import Job

from adhocracy.model import meta
from adhocracy.model.refs import to_ref, to_entity

log = getLogger(__name__)

LISTENERS = defaultdict(list)


class async(object):
    """
    An decorator that replaces rq's `.enqueue()` method that detects
    if it is running in a worker and takes care to cleanup after the
    job. You should not call `.enqueue() directly.

    Usage::

      >>> @async
      ... def afunc(arg):
      ...     return arg


    When you call the function you get back a :class:`rq.job.Job`
    proxy object (or a :class:`FakeJob` if no queue is available).

      >>> retval = afunc.enqueue('myarg')
    >>> isinstance(retval, job)
    """
    def __init__(self, func):
        self.func = func

    def enqueue(self, *args, **kwargs):
        '''
        Call this to guarante the function is enqueued.
        Mostly useful in a worker process where the function
        would be executed synchronously.
        '''
        queue = rq_config.queue
        if queue is None:
            return self.fake_job(*args, **kwargs)
        return queue.enqueue(self.func, *args, **kwargs)

    def fake_job(self, *args, **kwargs):
        fake_job = FakeJob()
        fake_job._result = self.func(*args, **kwargs)
        return fake_job

    def __call__(self, *args, **kwargs):
        '''
        Call this with the args and kwargs of the function you want
        to enqueue. It will queue the function and return a Job if
        a queue is available, or call the function syncronously
        and return a FakeJob if not.

        Returns:

        :class:`FakeJob`
          where `.return_value` will be the return value if *_force_sync*
          is True or we have no configured redis connection.
        :class:`rq.Job`
          if we do asyncronous processing.
        '''

        if rq_config.in_worker:
            try:
                log.debug('exec job from worker: args: %s, kwargs: %s' % (
                    str(args), str(kwargs)))
                return self.func(*args, **kwargs)
            except:
                #log.exception('exception in async.__call__')
                raise
            finally:
                # cleanup the sqlalchemy session after we run the job
                # from the queue.
                meta.Session.commit()
                meta.Session.remove()
        else:
            return self.enqueue(*args, **kwargs)


# --[ Redis configuration ]-------------------------------------------------

# config will be set from adhocracy.config.environment
# when the pylons application is initialized.

rq_config = None


class RQConfig(object):

    force_sync = False
    in_worker = False
    connection = None

    def __init__(self, host, port, queue_name):
        if not host or not port or not queue_name:
            log.warn(('You have not configured redis for adhocracy. '
                     'You should. Current configuration values:'
                      'host: %s, port: %s, name: %s') %
                     (host, port, queue_name))
            self.force_sync = True
            self.use_redis = False
            return
        self.host = host
        self.port = int(port)
        self.queue_name = queue_name
        self.use_redis = True
        self.connection = self.new_connection()

    def new_connection(self):
        if not self.use_redis:
            return None
        return Redis(host=self.host, port=self.port)

    @property
    def queue(self):
        if self.force_sync:
            return None
        return Queue(self.queue_name, connection=self.connection)

    @property
    def enqueue(self):
        queue = self.queue()
        if queue is None:
            return self.fake_job
        return queue.enqueue

    @classmethod
    def setup_from_config(cls, config):
        global rq_config
        rq_config = cls.from_config(config)

    @classmethod
    def from_config(cls, config):
        host = config.get('adhocracy.redis.host')
        port = config.get('adhocracy.redis.port')
        name = config.get('adhocracy.redis.queue')
        return cls(host, port, name)


# --[ async methods ]-------------------------------------------------------

def update_entity(entity, operation):
    entity_ref = to_ref(entity)
    if entity_ref is None:
        return
    data = dict(operation=operation, entity=entity_ref)
    data_json = json.dumps(data)
    return handle_update(data_json)


@async
def handle_update(message):
    data = json.loads(message)
    entity = to_entity(data.get('entity'))
    for (clazz, operation), listeners in LISTENERS.items():
        if operation != data.get('operation') \
           or not isinstance(entity, clazz):
            continue
        for listener in listeners:
            listener(entity)


@async
def minutely():
    from adhocracy.lib import democracy
    democracy.check_adoptions()


@async
def hourly():
    return
    # nothing here yet


@async
def daily():
    return
    from adhocracy.lib import watchlist
    watchlist.clean_stale_watches()


class FakeJob(Job):
    """
    FakeJob is meant to be used in settings where no redis queue is configured.
    It fakes the signature of a rq Job, but is executed synchronously.

    FIXME: This isn't working, as the signature of rq.job.Job constructor and
    other methods has changed.
    """

    _result = None

    @property
    def return_value(self):
        '''Override function to not connect to redis'''
