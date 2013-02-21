import json
from collections import defaultdict

from amqp import has_queue, post_message
from adhocracy.model.refs import to_ref, to_entity

UPDATE_SERVICE = 'entity'

LISTENERS = defaultdict(list)


def post_update(entity, operation):
    if has_queue():
        entity_ref = to_ref(entity)
        if entity_ref is None:
            return
        data = dict(operation=operation, entity=entity_ref)
        post_message(UPDATE_SERVICE, json.dumps(data))


def handle_update(message):
    data = json.loads(message)
    entity = to_entity(data.get('entity'))
    for (clazz, operation), listeners in LISTENERS.items():
        if (operation != data.get('operation')
                or not isinstance(entity, clazz)):
            continue
        for listener in listeners:
            listener(entity)
