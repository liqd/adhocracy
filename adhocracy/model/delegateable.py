import random 
from datetime import datetime
import logging

from sqlalchemy import Table, Column, Integer, Unicode, String, ForeignKey, DateTime, func, or_
from sqlalchemy.orm import relation, backref, mapper
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import meta
import filter as ifilter

log = logging.getLogger(__name__)

# REFACT: this should not be used anymore - remove?
category_graph = Table('category_graph', meta.data,
    Column('parent_id', Integer, ForeignKey('delegateable.id')),
    Column('child_id', Integer, ForeignKey('delegateable.id'))
    )

delegateable_table = Table('delegateable', meta.data,
    Column('id', Integer, primary_key=True),
    Column('label', Unicode(255), nullable=False),
    Column('type', String(50)),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=False)
    )

class Delegateable(object):
    
    def __init__(self):
        raise Exception("Make a category or a proposal instead!")
        
    def init_child(self, instance, label, creator):
        self.instance = instance
        self.label = label
        self.creator = creator
    
    def __repr__(self):
        return u"<Delegateable(%d,%s)>" % (self.id, self.instance.key)
    
    def is_super(self, delegateable):
        if delegateable in self.children:
            return True
        for child in self.children:
            r = child.is_super(delegateable)
            if r:
                return True
        return False
        
    def is_sub(self, delegateable):
        return delegateable.is_super(self)
    
    def is_mutable(self):
        return True
    
    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Delegateable)
            q = q.filter(Delegateable.id==int(id))
            if not include_deleted:
                q = q.filter(or_(Delegateable.delete_time==None,
                                 Delegateable.delete_time>datetime.utcnow()))
            if ifilter.has_instance() and instance_filter:
                q = q.filter(Delegateable.instance_id==ifilter.get_instance().id)
            return q.limit(1).first()
        except Exception, e: 
            log.warn("find(%s): %s" % (id, e))
            return None
        
    @classmethod    
    def all(cls, instance=None, include_deleted=False):
        q = meta.Session.query(Delegateable)
        if not include_deleted:
            q = q.filter(or_(Delegateable.delete_time==None,
                             Delegateable.delete_time>datetime.utcnow()))
        if instance is not None:
            q = q.filter(Delegateable.instance==instance)
        return q.all()
    
    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        if not self.is_deleted(delete_time):
            self.delete_time = delete_time
        for child in self.children:
            child.delete(delete_time=delete_time)
        for delegation in self.delegations:
            delegation.delete(delete_time=delete_time)
        for comment in self.comments:
            comment.delete(delete_time=delete_time)
        for poll in self.polls:
            poll.end()
            
    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
               self.delete_time<=at_time
               
    def find_latest_comment_time(self, recurse=True):
        from revision import Revision
        from comment import Comment
        try:
            topics = [self]
            if recurse:
                topics.extend(self.children)
            topics = map(lambda t: t.id, topics)
            query = meta.Session.query(Revision.create_time)
            query = query.join(Comment)
            query = query.filter(Comment.topic_id.in_(topics))
            query = query.order_by(Revision.create_time.desc())
            query = query.filter(Comment.canonical==False)
            query = query.limit(1)
            return query.first()[0]
        except: 
            log.exception("find_latest_comment(%s)" % self.id)
            return None
        
    def comment_count(self):
        return len(self.comments)
    
    def current_delegations(self):
        return filter(lambda d: not d.is_revoked(), self.delegations)
    
    def _index_id(self):
        return self.id
    
    def to_dict(self):
        return dict(id=self.id,
                    label=self.label,
                    instance=self.instance.key,
                    creator=self.creator.user_name,
                    create_time=self.create_time)


