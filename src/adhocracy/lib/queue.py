from collections import defaultdict
import json
from logging import getLogger

from pylons import config
from redis import Redis
from rq import Queue
from rq.job import Job

from adhocracy.model import meta
from adhocracy.model.refs import to_ref, to_entity

log = getLogger(__name__)

WORKER_CONFIG_KEY = u'adhocracy.rq.worker'
# save the thread save connection here
connection = None
queue_name = None

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
        queue = get_queue()
        return queue.enqueue(self.func, *args, **kwargs)

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
        queue = get_queue()

        if in_worker():
            try:
                return self.func(*args, **kwargs)
            finally:
                # cleanup the sqlalchemy session after we run the job
                # from the queue.
                meta.Session.commit()
                meta.Session.remove()

        if queue is None:
            fake_job = FakeJob()
            fake_job._result = self.func(*args, **kwargs)
            return fake_job

        self.enqueue(*args, **kwargs)


def in_worker(value=None):
    '''
    Get or set a config key to indicate that the process is a worker.
    '''
    if value is None:
        return config.get(WORKER_CONFIG_KEY, False)
    else:
        config[WORKER_CONFIG_KEY] = value


def get_queue():
    if connection is None:
        return None
    if queue_name is None:
        return None
    return Queue(queue_name, connection=connection)


def setup_redis_connection():
    host = config.get('adhocracy.redis.host')
    port = config.get('adhocracy.redis.port')
    name = config.get('adhocracy.redis.queue')

    if not (host and port and name):
        log.warn(('Could not get a valid configuration for redis. You should'
                  'use redis and configure adhocracy.redis.host, '
                  'adhocracy.redis.prot and adhocracy.redis.queue.\n'
                  'Current values: %s, %s, %s') % (host, port, name))
        return

    global connection, queue_name
    queue_name = name
    connection = Redis(host=host, port=int(port))


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
    return True


@async
def hourly():
    # nothing here yet
    return True


@async
def daily():
    from adhocracy.lib import watchlist
    watchlist.clean_stale_watches()
    return True


class FakeJob(Job):

    _result = None

    @property
    def return_value(self):
        '''Override function to not connect to redis'''
