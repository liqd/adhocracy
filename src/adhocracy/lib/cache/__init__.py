import inspect
import logging

from dogpile.cache import make_region
from dogpile.cache.region import _backend_loader
from dogpile.cache.backends.redis import RedisBackend

from  adhocracy import model
from adhocracy.lib import queue

from util import memoize

log = logging.getLogger(__name__)

HOUR = 60 * 60
TTL = HOUR * 3
TTL_TILES = HOUR * 6
TTL_MAX = max([TTL, TTL_TILES])
TTL_REDIS = TTL_MAX + HOUR

# --[ invalidation handlers ]-----------------------------------------------


def invalidate_badge(badge):
    log.debug('invalidate_badge %s' % badge)
    clear_tag(badge)


def invalidate_userbadges(userbadges):
    clear_tag(userbadges)
    invalidate_user(userbadges.user)


def invalidate_delegateablebadges(delegateablebadges):
    clear_tag(delegateablebadges)
    invalidate_delegateable(delegateablebadges.delegateable)


def invalidate_user(user):
    clear_tag(user)


def invalidate_text(text):
    clear_tag(text)
    invalidate_page(text.page)


def invalidate_page(page):
    invalidate_delegateable(page)


def invalidate_delegateable(d):
    clear_tag(d)
    for p in d.parents:
        invalidate_delegateable(p)
    if not len(d.parents):
        clear_tag(d.instance)


def invalidate_revision(rev):
    invalidate_comment(rev.comment)


def invalidate_comment(comment):
    clear_tag(comment)
    if comment.reply:
        invalidate_comment(comment.reply)
    invalidate_delegateable(comment.topic)


def invalidate_delegation(delegation):
    invalidate_user(delegation.principal)
    invalidate_user(delegation.agent)


def invalidate_vote(vote):
    clear_tag(vote)
    invalidate_user(vote.user)
    invalidate_poll(vote.poll)


def invalidate_selection(selection):
    if selection is None:
        return
    clear_tag(selection)
    if selection.page:
        invalidate_delegateable(selection.page)
    if selection.proposal:
        invalidate_delegateable(selection.proposal)


def invalidate_poll(poll):
    clear_tag(poll)
    if poll.action == poll.SELECT:
        invalidate_selection(poll.selection)
    elif isinstance(poll.subject, model.Delegateable):
        invalidate_delegateable(poll.subject)
    elif isinstance(poll.subject, model.Comment):
        invalidate_comment(poll.subject)


def invalidate_instance(instance):
    # muharhar cache epic fail
    clear_tag(instance)
    for d in instance.delegateables:
        invalidate_delegateable(d)


def invalidate_tagging(tagging):
    clear_tag(tagging)
    invalidate_delegateable(tagging.delegateable)


HANDLERS = {
    model.User: invalidate_user,
    model.Vote: invalidate_vote,
    model.Page: invalidate_page,
    model.Proposal: invalidate_delegateable,
    model.Delegation: invalidate_delegation,
    model.Revision: invalidate_revision,
    model.Comment: invalidate_comment,
    model.Poll: invalidate_poll,
    model.Tagging: invalidate_tagging,
    model.Text: invalidate_text,
    model.Selection: invalidate_selection,
    model.Badge: invalidate_badge,
    model.UserBadges: invalidate_userbadges,
    model.DelegateableBadges: invalidate_delegateablebadges
}


def invalidate(entity):
    try:
        from pylons import app_globals as g
        if g.cache is not None:
            func = HANDLERS.get(entity.__class__, lambda x: x)
            func(entity)
    except TypeError:
        pass


# --[ Cache Handling ]------------------------------------------------------


class CacheTagging(object):
    '''
    Book keeping for Objects and cache keys. It maintains a mapping
    from Objects used as discriminators in memoized functions to entries
    in the cache.

    Each object is generated a universally valid tag. This depends on
    the object to return a suitable unicode() or repr() value.

    These tags become part of the cache key and we mainain a tag -> cache keys
    mapping.
    '''

    @staticmethod
    def make_tag(obj):
        '''
        create a tag for obj.

        Returns: 2-tuple of (tag (unicode), handled (boolean)) where
        handled indicates if we have an invalidation handler for the object.
        '''
        # module = getattr(obj, '__module__', 'no module')
        # log.debug('make tag.\n * module: %s\n * obj: %s' % (module, obj))

        try:
            tag = unicode(obj)
        except:
            tag = repr(obj)

        # cache tags that contain memory address are useless.
        if 'at 0x' in tag:
            raise ValueError(('tag %s for object not suitable for '
                              'cache tagging.') % tag)

        obj_class = getattr(obj, '__class__', None)
        return (tag, obj_class in HANDLERS)

    @classmethod
    def key_generator(cls, namespace, fn):
        '''
        A key generator that can be passed to a dogpile.cache region.

        It returns a function that generates a key based on the signature
        of the function *fn* to cache. *namespace* is an arbitrary prefix
        for the key that can be set when the *<region>.cache_on_arguments*
        decorator is used.

        This function add the key to a set of keys for every object
        in the arguments.
        '''

        prefix = '%s:%s' % (fn.__module__, fn.__name__)

        if namespace is not None:
            prefix = "%s|%s" % (prefix, namespace)

        [argnames, _, _, _] = inspect.getargspec(fn)
        has_self = (argnames[0] in ('self', 'cls')) if argnames else False

        def make_key(*args, **kwargs):
            if has_self:
                args = args[1:]
            tags = []
            key = prefix
            for arg in args:
                tag, handled = cls.make_tag(arg)
                if handled:
                    tags.append(tag)
                key = key + '||' + tag
            for keyword, value in kwargs.items():
                tag, handled = cls.make_tag(value)
                if handled:
                    tags.append(tag)
                key = key + "||%s::%s" % (keyword, tag)

            # remember the key for all tags so we can invalidate them
            # later
            redis = queue.rq_config.new_connection()
            if redis is not None:
                with redis.pipeline() as pipe:
                    for tag in tags:
                        print tag
                        pipe.sadd(tag, key)
                    pipe.execute()
            # log.debug("\nkey - length: %6s :: %s" % (len(key), key))
            return key
        return make_key

    @classmethod
    def clear_tag(cls, obj):
        '''
        Remove all entries in the cache for the given object.
        '''
        tag = cls.make_tag(obj)
        redis = queue.rq_config.new_connection()
        if redis is not None:
            return
        with redis.pipeline() as pipe:
            keys = pipe.smembers(tag)
            pipe.delete(keys)
            pipe.execute()

# b/w compat for now. FIXME: refactor
clear_tag = CacheTagging.clear_tag


class RedisDebugCacheBackend(RedisBackend):

    def get(self, key):
        # log.debug('\ncache - get: ' + key)
        value = super(RedisDebugCacheBackend, self).get(key)
        log.debug('\nVALUE: %s' % unicode(value)[:50] + '...')
        return value

    def set(self, key, value):
        # log.debug('\ncache - set: ' + key)
        return super(RedisDebugCacheBackend, self).set(key, value)

    def delete(self, key):
        # log.debug('\ncache - delete: %s' % key)
        return super(RedisDebugCacheBackend, self).delete(key)

BACKEND_NAME = "docpile.cache.adhocracyredis"
_backend_loader.impls[BACKEND_NAME] = lambda: RedisDebugCacheBackend


template_region = make_region(
    function_key_generator=CacheTagging.key_generator).configure(
        BACKEND_NAME,
        expiration_time=60 * 60,
        arguments={'url': ["127.0.0.1"],
                   'port': 5006,
                   'redis_expiration_time': TTL_REDIS,
                   'distributed_lock': True})
