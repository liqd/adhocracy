from datetime import datetime
import logging

from sqlalchemy import Table, Column, Integer, Unicode, ForeignKey, DateTime, func
from sqlalchemy.orm import reconstructor, aliased

import meta
import instance_filter as ifilter

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
        return "<Tag(%s,%s)>" % (self.id, self.name.encode('ascii', 'replace'))
    
    
    def __unicode__(self):
        return self.name
    
    
    def __len__(self):
        if self._count is None:
            from tagging import Tagging 
            from delegateable import Delegateable
            q = meta.Session.query(Tagging)
            q = q.filter(Tagging.tag==self)
            if ifilter.has_instance():
                q = q.join(Delegateable)
                q = q.filter(Delegateable.instance_id==ifilter.get_instance().id)
            self._count = q.count()
        return self._count
        
    count = property(__len__)
    
    
    def __le__(self, other):
        return self.name >= other.name 
    
    
    def __lt__(self, other):
        return self.name > other.name
    
    
    @classmethod
    def by_id(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Tag)
            q = q.filter(Tag.id==id)
            return q.limit(1).first()
        except Exception, e:
            log.warn("by_id(%s): %s" % (id, e))
            return None
    

    @classmethod
    def find(cls, name, instance_filter=True, include_deleted=False):
        import adhocracy.lib.text as text
        name = text.tag_normalize(name)
        try:
            q = meta.Session.query(Tag)
            try: 
                id = int(name)
                q = q.filter(Tag.id==id)
            except ValueError:
                q = q.filter(Tag.name.like(name))
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (name, e))
            return None

    
    
    @classmethod
    def all(cls):
        q = meta.Session.query(Tag)
        return q.all()
        
    
    @classmethod
    def popular_tags(cls, limit=None):
        from tagging import Tagging, tagging_table
        from delegateable import Delegateable
        q = meta.Session.query(Tag)
        q = q.add_column(func.count(Tagging.id))
        q = q.join(Tagging)
        if ifilter.has_instance():
            q = q.join(Delegateable)
            q = q.filter(Delegateable.instance_id==ifilter.get_instance().id)
        q = q.group_by(Tag.id, Tag.create_time, Tag.name)
        q = q.order_by(func.count(Tagging.id).desc())
        # SQLAlchemy turns this into a fucking subquery:
        #if limit is not None: 
        #    q = q.limit(limit)
        #print "QUERY", q
        return q.all()[:limit]
        
    
    @classmethod
    def similar_tags(cls, tag, limit=None):
        from tagging import Tagging, tagging_table
        from delegateable import Delegateable
        q = meta.Session.query(Tag)
        q = q.add_column(func.count(Tagging.id))
        fst_tagging = aliased(Tagging)
        q = q.join(fst_tagging, Tag.taggings)
        q = q.join((Delegateable, fst_tagging.delegateable))
        snd_tagging = aliased(Tagging)
        q = q.join((snd_tagging, Delegateable.taggings))
        q = q.filter(snd_tagging.tag_id==tag.id)
        q = q.filter(Tag.id!=tag.id)
        if ifilter.has_instance():
            q = q.filter(Delegateable.instance_id==ifilter.get_instance().id)
        q = q.group_by(Tag.id, Tag.create_time, Tag.name)
        q = q.order_by(func.count(Tagging.id).desc())
        # SQLAlchemy turns this into a fucking subquery:
        #if limit is not None: 
        #    q = q.limit(limit)
        return q.all()[:limit]
        
    
    @classmethod
    def complete(cls, prefix, limit=5, instance_filter=True):
        from tagging import Tagging, tagging_table
        from delegateable import Delegateable
        q = meta.Session.query(Tag)
        q = q.add_column(func.count(Tagging.id))
        q = q.join(Tagging)
        q = q.filter(func.lower(Tag.name).like(prefix.lower() + "%"))
        if ifilter.has_instance() and instance_filter:
            q = q.join(Delegateable)
            q = q.filter(Delegateable.instance_id==ifilter.get_instance().id)
        q = q.group_by(Tag.id, Tag.create_time, Tag.name)
        q = q.order_by(func.count(Tagging.id).desc())
        # SQLAlchemy turns this into a fucking subquery:
        #if limit is not None: 
        #    q = q.limit(limit)
        #print "QUERY", q
        return q.all()[:limit]
        
        
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
    
    
    def to_dict(self):
        from adhocracy.lib import url
        return dict(id=self.id,
                    name=self.name,
                    count=self.count,
                    url=url.entity_url(self))
    
    
    def _index_id(self):
        return self.id
        

