import random 
from datetime import datetime
import logging

from sqlalchemy import Table, Column, Integer, Unicode, String, ForeignKey, DateTime, func, or_
from sqlalchemy.orm import relation, backref
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import meta
import filter
from meta import Base
from user import User

log = logging.getLogger(__name__)

# REFACT: this should not be used anymore - remove?
category_graph = Table('category_graph', Base.metadata,
    Column('parent_id', Integer, ForeignKey('delegateable.id')),
    Column('child_id', Integer, ForeignKey('delegateable.id'))
    )

class Delegateable(Base):    
    __tablename__ = 'delegateable'
    
    id = Column(Integer, primary_key=True)
    label = Column(Unicode(255), nullable=False)
    delgateable_type = Column('type', String(50))
    
    create_time = Column(DateTime, default=datetime.utcnow)
    access_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    delete_time = Column(DateTime, nullable=True)
    
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    creator = relation(User, 
        primaryjoin="Delegateable.creator_id==User.id", 
        backref=backref('delegateables', cascade='delete'))
    
    instance_id = Column(Integer, ForeignKey('instance.id'), nullable=False)
    instance = relation('Instance', lazy=True,
        primaryjoin="Delegateable.instance_id==Instance.id", 
        backref=backref('delegateables', cascade='delete'))
    
    __mapper_args__ = {'polymorphic_on': delgateable_type,
                       'extension': Base.__mapper_args__.get('extension')}
    
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
    
    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Delegateable)
            q = q.filter(Delegateable.id==id)
            if not include_deleted:
                q = q.filter(or_(Delegateable.delete_time==None,
                                 Delegateable.delete_time>datetime.utcnow()))
            if filter.has_instance() and instance_filter:
                q = q.filter(Delegateable.instance_id==filter.get_instance().id)
            return q.one()
        except: 
            log.exception("find(%s)" % id)
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
            
    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
               self.delete_time<=at_time
    
    def _index_id(self):
        return self.id
    
Delegateable.__mapper__.add_property('parents', relation(Delegateable, lazy=True, secondary=category_graph, 
    primaryjoin=Delegateable.__table__.c.id == category_graph.c.parent_id,
    secondaryjoin=category_graph.c.child_id == Delegateable.__table__.c.id))
    
Delegateable.__mapper__.add_property('children', relation(Delegateable, lazy=True, secondary=category_graph, 
    primaryjoin=Delegateable.__table__.c.id == category_graph.c.child_id,
    secondaryjoin=category_graph.c.parent_id == Delegateable.__table__.c.id))