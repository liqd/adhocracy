import logging
from datetime import datetime

from adhocracy import model
from adhocracy.model import hooks
from adhocracy.model import refs
from .. import text 

from index import get_index

def datetime2str(dt):
    return unicode(dt.strftime("%s"))

def index_entity(entity):
    return {'ref': refs.to_ref(entity),
            'doc_type': refs.entity_type(entity)}

def index_user(entity):
    d = index_entity(entity)
    d['title'] = entity.name
    if entity.bio:
        d['text'] = entity.bio
    d['create_time'] = datetime2str(entity.create_time)
    return d

def index_comment(entity):
    d = index_entity(entity)
    d['user'] = " ".join((entity.latest.user.name, 
                          entity.creator.name))
    d['create_time'] = datetime2str(entity.latest.create_time)
    d['text'] = entity.latest.text
    d['instance'] = entity.topic.instance.key
    return d

def index_delegateable(entity):
    d = index_entity(entity)
    d['title'] = entity.label
    d['create_time'] = datetime2str(entity.create_time)
    d['user'] = entity.creator.name
    d['instance'] = entity.instance.key
    return d

def index_category(entity):
    return index_delegateable(entity)

def index_issue(entity):
    d = index_delegateable(entity)
    d['text'] = entity.comment.latest.text
    return d

def index_motion(entity):
    d = index_delegateable(entity)
    text = entity.comment.latest.text if entity.comment else ""
    for comment in entity.comments:
        if comment.canonical:
            text += " " + comment.latest.text
    d['text'] = text
    return d

def insert(index_func):
    def f(entity):
        writer = get_index().writer()
        writer.add_document(**index_func(entity))
        writer.commit()
    return f

def update(index_func):
    def f(entity):
        writer = get_index().writer()
        writer.update_document(**index_func(entity))
        writer.commit()
    return f

def delete():
    def f(entity):
        ix = get_index()
        ref = refs.to_ref(entity)
        ix.delete_by_term('ref', ref)
        ix.commit()
    return f

def register_indexer(cls, index_func):
    hooks.patch(cls, hooks.POSTINSERT, insert(index_func))
    hooks.patch(cls, hooks.POSTUPDATE, update(index_func))
    hooks.patch(cls, hooks.PREDELETE, delete())

