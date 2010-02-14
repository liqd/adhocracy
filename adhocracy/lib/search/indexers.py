import logging
from datetime import datetime

from adhocracy import model
from adhocracy.model import hooks
from adhocracy.model import refs
from .. import text 

from index import get_index, ix_lock

def datetime2str(dt):
    return unicode(dt.strftime("%s"))

def index_entity(entity):
    return {'ref': refs.to_ref(entity),
            'doc_type': refs.entity_type(entity)}

def index_user(entity):
    if entity.is_deleted():
        return None
    d = index_entity(entity)
    d['title'] = entity.name
    if entity.bio:
        d['text'] = entity.bio if entity.bio is not None else u''
    ct = datetime2str(entity.create_time if \
                      entity.create_time else datetime.utcnow())
    d['create_time'] = ct
    d['user'] = " ".join((entity.name, 
                          entity.user_name))
    return d

def index_comment(entity):
    if entity.is_deleted():
        return None
    d = index_entity(entity)
    if entity.latest:
        d['user'] = " ".join((entity.latest.user.name, 
                              entity.creator.name))
        d['text'] = entity.latest.text
    else:
        d['user'] = d['text'] = u""
    ct = datetime2str(entity.latest.create_time if \
            entity.latest else datetime.utcnow())
    d['create_time'] = ct
    d['instance'] = entity.topic.instance.key
    return d

def index_delegateable(entity):
    if entity.is_deleted():
        return None
    d = index_entity(entity)
    d['title'] = entity.label
    ct = datetime2str(entity.create_time if \
                      entity.create_time else datetime.utcnow())
    d['create_time'] = ct
    d['user'] = entity.creator.name
    d['instance'] = entity.instance.key
    d['text'] = ' '.join(map(lambda c: c.latest.text, entity.comments))
    return d

def index_issue(entity):
    if entity.is_deleted():
        return None
    d = index_delegateable(entity)
    return d

def index_proposal(entity):
    if entity.is_deleted():
        return None
    d = index_delegateable(entity)
    return d

def insert(index_func):
    def f(entity):
        entry = index_func(entity)
        if entry is None:
            delete(entity)
        else:
            ix_lock.acquire()
            try:
                writer = get_index().writer()
                writer.add_document(**entry)
                writer.commit()
            finally:
                ix_lock.release()            
    return f

def update(index_func):
    def f(entity):
        entry = index_func(entity)
        if entry is None:
            delete(entity)
        else:
            ix_lock.acquire()
            try:
                writer = get_index().writer()
                writer.update_document(**entry)
                writer.commit()
            finally:
                ix_lock.release()
    return f

def delete(entity):
    ix_lock.acquire()
    try:
        ix = get_index()
        ref = refs.to_ref(entity)
        ix.delete_by_term('ref', ref)
        ix.commit()
    finally:
        ix_lock.release()


