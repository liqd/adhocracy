from datetime import datetime
import logging
from itertools import count

from sqlalchemy import Table, Column, Integer, Unicode, ForeignKey, DateTime, func, or_
from sqlalchemy.orm import relation, backref

import meta
import instance_filter as ifilter

log = logging.getLogger(__name__)


page_table = Table('page', meta.data,                      
    Column('id', Integer, primary_key=True),
    Column('alias', Unicode(255), nullable=False),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime)
    )


class Page(object):
    
    def __init__(self, instance, alias, user):
        self.alias = alias
        self.user = user
        self.instance = instance
    
    
    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Page)
            try:
                id = int(id)
                q = q.filter(Page.id==id)
            except ValueError:
                q = q.filter(Page.alias==id)
            if not include_deleted:
                q = q.filter(or_(Page.delete_time==None,
                                 Page.delete_time>datetime.utcnow()))
            if ifilter.has_instance() and instance_filter:
                q = q.filter(Page.instance==ifilter.get_instance())
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None


    @classmethod
    def all(cls, instance=None, include_deleted=False):
        q = meta.Session.query(Page)
        if not include_deleted:
            q = q.filter(or_(Page.delete_time==None,
                             Page.delete_time>datetime.utcnow()))
        q = q.filter(Page.instance==instance)
        return q.all()
    
    
    @classmethod
    def free_alias(cls, title):
        from adhocracy.lib.text import title2alias
        alias = title2alias(title)
        for i in count(0):
            if i == 0: test = alias
            else: test = alias + str(i)
            page = Page.find(test)
            if page is None: 
                return test
    
    
    @classmethod
    def create(cls, instance, title, text, user):
        from text import Text
        alias = Page.free_alias(title)
        page = Page(instance, alias, user)
        meta.Session.add(page)
        meta.Session.flush()
        _text = Text(page, Text.HEAD, user, title, text)
        return page
    
    
    def _get_variants(self):
        return list(set([t.variant for t in self.texts]))
        
    variants = property(_get_variants)
    
    
    def variant_head(self, variant):
        for text in self.texts:
            if text.variant == variant:
                return text
        return None
    
    
    def variant_history(self, variant):
        history = []
        for text in self.texts:
            if text.variant == variant:
                history.append(text)
        return history
    
    
    def _get_heads(self):
        return [self.variant_head(h) for h in self.variants]
    
    heads = property(_get_heads)
    
    
    def _get_head(self):
        from text import Text
        return self.variant_head(Text.HEAD)
        
    head = property(_get_head)
    
    
    def _get_title(self):
        return self.head.title
        
    title = property(_get_title)
    label = property(_get_title)
    
    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        for text in self.texts:
            text.delete(delete_time=delete_time)
        if self.delete_time is None:
            self.delete_time = delete_time
    
    
    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
               self.delete_time<=at_time
    
    
    def _index_id(self):
        return self.id
    
    
    def to_dict(self):
        from adhocracy.lib import url
        return dict(id=self.id,
                    url=url.entity_url(self),
                    create_time=self.create_time,
                    alias=self.alias,
                    user=self.user.user_name)
    
    
    def __repr__(self):
        return u"<Page(%s, %s)>" % (self.id, self.alias)
    
