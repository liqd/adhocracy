# http://www.mail-archive.com/sqlalchemy@googlegroups.com/msg09203.html
import logging
import simplejson
from sqlalchemy.orm import MapperExtension, EXT_CONTINUE

log = logging.getLogger(__name__)

SERVICE = 'entity'
PREINSERT = "_pre_insert"
PREDELETE = "_pre_delete"
PREUPDATE = "_pre_update"
POSTINSERT = "_post_insert"
POSTDELETE = "_post_delete"
POSTUPDATE = "_post_update"
REGISTRY = {}


class HookExtension(MapperExtension):
    """ Extention to add pre-commit hooks.

    Hooks will be called in Mapped classes if they define any of these
    methods:
      * _pre_insert()
      * _pre_delete()
      * _pre_update()
    """

    def before_insert(self, mapper, connection, instance):
        if getattr(instance, PREINSERT, None):
            instance._pre_insert()
        return EXT_CONTINUE

    def before_delete(self, mapper, connection, instance):
        if getattr(instance, PREDELETE, None):
            instance._pre_delete()
        return EXT_CONTINUE

    def before_update(self, mapper, connection, instance):
        if getattr(instance, PREUPDATE, None):
            instance._pre_update()
        return EXT_CONTINUE

    def after_insert(self, mapper, connection, instance):
        if getattr(instance, POSTINSERT, None):
            instance._post_insert()
        return EXT_CONTINUE

    def after_delete(self, mapper, connection, instance):
        if getattr(instance, POSTDELETE, None):
            instance._post_delete()
        return EXT_CONTINUE

    def after_update(self, mapper, connection, instance):
        if getattr(instance, POSTUPDATE, None):
            instance._post_update()
        return EXT_CONTINUE


def patch_some(clazz, hooks, f):
    for hook in hooks:
        patch(clazz, hook, f)


def patch_pre(clazz, f):
    patch_some(clazz, [PREINSERT, PREUPDATE, PREDELETE], f)


def patch_post(clazz, f):
    patch_some(clazz, [POSTINSERT, POSTUPDATE, POSTDELETE], f)


def patch_default(clazz, f):
    patch_some(clazz, [POSTINSERT, POSTUPDATE, PREDELETE], f)


def patch(clazz, hook, f):
    prev = getattr(clazz, hook, None)
    a = f
    if prev:
        def chain(*a, **kw):
            f(*a, **kw)
            prev(*a, **kw)
        a = chain
    setattr(clazz, hook, a)


def register_queue_callback(cls, event, callback):
    import refs
    key = (refs.cls_type(cls), event)
    calls = REGISTRY.get(key, [])
    calls.append(callback)
    REGISTRY[key] = calls


def handle_queue_message(message):
    import refs
    data = simplejson.loads(message)
    entity = refs.to_entity(data.get('entity'))
    try:
        for signature, calls in REGISTRY.items():
            (r_type, r_event) = signature
            if r_event == data.get('event') and \
                r_type == refs.entity_type(entity):
                for callback in calls:
                    callback(entity)
    except:
        log.exception("Failed to handle message: %s" % message)


def init_queue_hooks():
    '''Patch pre_* and post_* functions into all model classes listed.
    in :data:`adhocracy.model.refs.TYPES`. The patched in function
    will add messages to the job queue used to defer external indexing.
    These will be called by :class:`HookExtension` before and after
    changed models are commited to the database.

    ..Warning::

    Some of the patched in functions for :class:`adhocracy.model.Vote`
    and  :class:`adhocracy.model.Delegation` will be overwritten by
    :func:`adhocracy.lib.democracy.init_democracy`
    '''
    from adhocracy.lib.queue import has_queue, post_message
    import refs
    types_list = sorted([repr(t) for t in refs.TYPES])
    log.debug('PATCHING model classes with pre_* and post_* functions for '
              ' queue handling to be used in pre/post commit hooks. '
              'patched:\n%s' % ('\n'.join(types_list)))
    for cls in refs.TYPES:
        for event in [PREINSERT, PREDELETE, PREUPDATE, POSTINSERT,
                      POSTDELETE, POSTUPDATE]:
            def _handle_event(entity):
                if has_queue():
                    entity_ref = refs.to_ref(entity)
                    data = dict(event=event, entity=entity_ref)
                    post_message(SERVICE, simplejson.dumps(data))
            patch(cls, event, _handle_event)
