from collections import defaultdict
import json
from logging import getLogger

# from decorator import decorator
from pylons import config
from redis import Redis
from rq import Queue
from rq.job import Job

from adhocracy.model import meta
from adhocracy.model.refs import to_ref, to_entity

log = getLogger(__name__)
LISTENERS = defaultdict(list)
# save the thread save connection here
connection = None
queue_name = None


# @decorator
# def async(func, *args, **kwargs):
#     """
#     Use this instead of :meth:`rq.Queue.enqueue`.

#     A function (usabla as a decorator) to turn a function call into an
#     async rq job.  It takes care to cleanup after the job which is not
#     done by the worker otherwise.  It will fall back to syncronous
#     execution if there is no connection or the kwarg *_force_sync* is
#     True.

#     *_force_sync*
#        Do not try to put the job into a queue but execute it right
#        away.
#     *_from_queue*
#        Execute the function and return it's return value instead of
#        a `Job`. Use this only to run from the queue.

#     Returns:

#     :class:`FakeJob`
#       where `.return_value` will be the return value if *_force_sync*
#       is True or we have no configured redis connection.
#     :class:`rq.Job`
#       if we do asyncronous processing.
#     The return value of *func*
#       if it is run with *_from_queue* == True
#     """
#     queue = get_queue()
#     _force_sync = kwargs.pop('_force_sync', False)
#     _from_queue = kwargs.pop('_from_queue', False)
#     if _force_sync or (queue is None):
#         fake_job = FakeJob()
#         fake_job._result = func(*args, **kwargs)
#         return fake_job
#     elif _from_queue:
#         clean_args = args
#         clean_kwargs = kwargs
#         try:
#             return func(*clean_args, **clean_kwargs)
#         finally:
#             # cleanup the sqlalchemy session after we run the job from the
#             # queue.
#             meta.Session.remove()
#     else:
#         return queue.enqueue(func, *args, _from_queue=True, **kwargs)


class async(object):
    """
    An decorator that adds an .enqueue() method and takes care to cleanup
    after the job.

    You can decorate functions with this decorator like this::

      >>> @async
      ... def afunc(arg):
      ...     return arg

    and defer it into a queue. You get back a :class:`rq.job.Job`
    proxy object (or a :class:`FakeJob` if no queue is available).

      >>> retval = afunc.enqueue('myarg')
      >>> isinstance(retval, job)
    """
    def __init__(self, func):
        self.func = func

    def enqueue(self, *args, **kwargs):
        '''
        Call this with the args and kwargs of the function you
        enqueue. It will queue the function and return a Job if
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
        _force_sync = kwargs.pop('_force_sync', False)
        if _force_sync or (queue is None):
            fake_job = FakeJob()
            fake_job._result = self.func(*args, **kwargs)
            return fake_job
        else:
            return queue.enqueue(self.func, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        try:
            return self.func(*args, **kwargs)
        finally:
            # cleanup the sqlalchemy session after we run the job from the
            # queue.
            meta.Session.remove()


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


def update_entity(entity, operation):
    entity_ref = to_ref(entity)
    if entity_ref is None:
        return
    data = dict(operation=operation, entity=entity_ref)
    data_json = json.dumps(data)
    return handle_update.enqueue(data_json)


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
