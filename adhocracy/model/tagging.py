from datetime import datetime
import logging

from sqlalchemy import Table, Column, Integer, Unicode, ForeignKey, DateTime, func

import meta
import filter as ifilter

log = logging.getLogger(__name__)

tagging_table = Table('tagging', meta.data, 
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('tag_id', Integer, ForeignKey('tag.id'), nullable=False),
    Column('delegateable_id', Integer, ForeignKey('delegateable.id'), nullable=False),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    )

class Tagging(object):
    
    def __init__(self, delegateable, tag, creator):
        self.delegateable = delegateable
        self.tag = tag
        self.creator = creator
    
    
    def __repr__(self):
        return "<Tagging(%s,%s,%s,%s)>" % (self.id, self.delegateable.id,
                                     self.tag.name, tag.creator.user_name)
    
    
    @classmethod
    def find_by_delegateable_name_creator(cls, delegateable, name, creator):
        import adhocracy.lib.text as text
        name = text.tag_normalize(name)
        try:
            q = meta.Session.query(Tagging)
            q = q.filter(Tagging.creator==creator)
            q = q.filter(Tagging.delegateable==delegateable)
            q = q.join(Tag)
            q = q.filter(Tag.name.like(name))
            return q.limit(1).first()
        except Exception, e:
            log.warn("find_by_delegateable_name_creator(%s): %s" % (id, e))
            return None
    
    
    @classmethod
    def create(cls, delegateable, tag, creator):
        from tag import Tag
        if not isinstance(tag, Tag):
            tag = Tag.find_or_create(tag)
        tagging = Tagging(delegateable, tag, creator)
        meta.Session.add(tagging)
        meta.Session.flush()
        return tagging


