import logging
from sqlalchemy.orm import SessionExtension

log = logging.getLogger(__name__)

DELETE = "delete"
INSERT = "insert"
UPDATE = "update"

REGISTRY = {}


class SessionModificationExtension(SessionExtension):
    '''
    A sqlalchemy SessionExtension to do work before commit, like
    invalidating caches and adding asynchronous tasks.
    '''

    def before_flush(self, session, flush_context, instances):
        if not hasattr(session, '_object_cache'):
            session._object_cache = {INSERT: set(),
                                     DELETE: set(),
                                     UPDATE: set()}
        session._object_cache[INSERT].update(session.new)
        session._object_cache[DELETE].update(session.deleted)
        session._object_cache[UPDATE].update(session.dirty)

    def before_commit(self, session):
        from adhocracy.lib import cache

        session.flush()
        if not hasattr(session, '_object_cache'):
            return

        for operation, entities in session._object_cache.items():
            for entity in entities:
                self.post_update(entity, operation)

        #for entity in session._object_cache[INSERT]:

        for entity in session._object_cache[UPDATE]:
            cache.invalidate(entity)

        for entity in session._object_cache[DELETE]:
            cache.invalidate(entity)

        del session._object_cache

    def post_update(self, entity, operation):
        '''
        Post an update task for the entity and any related objects.
        '''
        from adhocracy import model
        from adhocracy.lib import queue
        queue.update_entity(entity, operation)

        ## Do subsequent updates to reindex related content
        # NOTE: This may post duplicate update tasks if an entity
        # is part of the session, and also updated depending on
        # another entity. Ignored for now cause the real work
        # is asynchronous and (probably) not expensive.
        # NOTE: Move the decisions about which other objects to
        # update to the models
        if isinstance(entity, model.Poll):
            queue.update_entity(entity.scope, UPDATE)
