# http://www.mail-archive.com/sqlalchemy@googlegroups.com/msg09203.html
import logging
import json
from sqlalchemy.orm import MapperExtension, SessionExtension, EXT_CONTINUE
from sqlalchemy.orm.session import Session

log = logging.getLogger(__name__)

DELETE = "delete"
INSERT = "insert"
UPDATE = "update"

REGISTRY = {}

class SessionModificationExtension(SessionExtension):

    def before_flush(self, session, flush_context, instances):
        if not hasattr(session, '_object_cache'):
            session._object_cache= {INSERT: set(),
                                    DELETE: set(),
                                    UPDATE: set()}
        session._object_cache[INSERT].update(session.new)
        session._object_cache[DELETE].update(session.deleted)
        session._object_cache[UPDATE].update(session.dirty)

    def before_commit(self, session):
        from adhocracy.lib import cache
        from adhocracy.lib import queue

        session.flush()
        if not hasattr(session, '_object_cache'):
            return

        for operation, entities in session._object_cache.items():
            for entity in entities:
                queue.post_update(entity, operation)

        #for entity in session._object_cache[INSERT]:

        for entity in session._object_cache[UPDATE]:
            cache.invalidate(entity)

        for entity in session._object_cache[DELETE]:
            cache.invalidate(entity)

        del session._object_cache



