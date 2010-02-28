from datetime import datetime
import logging

from sqlalchemy import Table, Column, Integer, Unicode, ForeignKey, DateTime, func
from sqlalchemy.orm import reconstructor

import meta
import filter as ifilter

log = logging.getLogger(__name__)

tag_table = Table('tag', meta.data, 
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('name', Unicode(255), nullable=False)
    )

class Tag(object):
    
    def __init__(self, name):
        self.name = name
        self._count = None
    
    
    @reconstructor
    def _reconstruct(self):
        self._count = None
    
    
    def __repr__(self):
        return "<Tag(%s,%s)>" % (self.id, self.name)
    
    
    def __unicode__(self):
        return self.name
    
    
    def __len__(self):
        if self._count is None:
            from tagging import Tagging 
            q = meta.Session.query(Tagging)
            q = q.filter(Tagging.tag==self)
            if filter.has_instance():
                q = q.join(Delegateable)
                q = q.filter(Delegateable.instance_id==filter.get_instance().id)
            self._count = q.count()
        return self._count
        
    count = property(__len__)
    
    
    @classmethod
    def find(cls, name, instance_filter=True, include_deleted=False):
        import adhocracy.lib.text as text
        name = text.tag_normalize(name)
        try:
            q = meta.Session.query(Tag)
            q = q.filter(Tag.name.like(name))
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None
    
    
    @classmethod
    def all(cls):
        q = meta.Session.query(Tag)
        return q.all()
        
        
    @classmethod
    def create(cls, name):
        import adhocracy.lib.text as text
        tag = Tag(text.tag_normalize(name))
        meta.Session.add(tag)
        meta.Session.flush()
        return tag
    
    
    @classmethod
    def find_or_create(cls, name):
        tag = Tag.find(name)
        if tag is None:
            tag = Tag.create(name)
        return tag

