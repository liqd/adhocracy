import logging
import simplejson

log = logging.getLogger(__name__)

from amqp import has_queue, post_message, read_messages
import adhocracy.model.refs as refs
import adhocracy.model.hooks as hooks

QUEUE = 'entity'
INSERT = 'insert'
UPDATE = 'update'
DELETE = 'delete'
REGISTRY = {}


def register(cls, event, callback):
    key = (refs.cls_type(cls), event)
    calls = REGISTRY.get(key, [])
    calls.append(callback)
    REGISTRY[key] = calls

def _process(event, entity):
    #log.debug("Handling %s hooks of %s" % (event, entity))
    for signature, calls in REGISTRY.items():
        (r_type, r_event) = signature
        if r_event == event and \
            r_type == refs.entity_type(entity):
            for callback in calls: 
                callback(entity)

def process_messages():
    if not has_queue():
        return
    
    def handle_message(message):
        data = simplejson.loads(message)
        entity = refs.to_entity(data.get('entity'))
        try:
            _process(data.get('event'), entity)
        except:
            log.exception("Failed to handle message: %s" % message)
    
    read_messages(QUEUE, handle_message)

def handle(event):
    def _call(entity):
        if has_queue():
            entity_ref = refs.to_ref(entity)
            data = dict(event=event, entity=entity_ref)
            post_message(QUEUE, simplejson.dumps(data))
    return _call

def init_hooks():
    for cls in refs.TYPES:
        hooks.patch(cls, hooks.POSTINSERT, handle(INSERT))
        hooks.patch(cls, hooks.POSTUPDATE, handle(UPDATE))
        hooks.patch(cls, hooks.PREDELETE, handle(DELETE))

    