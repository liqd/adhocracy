import re
from datetime import datetime
import logging

from sqlalchemy import Column, Integer, Float, Unicode, UnicodeText, ForeignKey, DateTime, func, or_
from sqlalchemy.orm import relation, synonym, backref

import meta
from meta import Base
import user

log = logging.getLogger(__name__)

# Instance is not a delegateable - but it should - or you cannot do instance wide delegation
class Instance(Base):
    __tablename__ = 'instance'
    
    INSTANCE_KEY = re.compile("^[a-zA-Z][a-zA-Z0-9_]{2,18}$")
    
    id = Column(Integer, primary_key=True)
    _key = Column('key', Unicode(20), nullable=False, unique=True)
    label = Column(Unicode(255), nullable=False)
    description = Column(UnicodeText(), nullable=True)
    
    required_majority = Column(Float, nullable=False)
    activation_delay = Column(Integer, nullable=False)
    
    create_time = Column(DateTime, default=func.now())
    access_time = Column(DateTime, default=func.now(), onupdate=func.now())
    delete_time = Column(DateTime, nullable=True)
    
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    creator = relation(user.User, 
        primaryjoin="Instance.creator_id==User.id", 
        backref=backref('created_instances'))
    
    default_group_id = Column(Integer, ForeignKey('group.id'), nullable=True)
    default_group = relation('Group', lazy=True)
        
    def __init__(self, key, label, creator, description=None):
        self.key = key
        self.label = label
        self.creator = creator
        self.description = description
        self.required_majority = 0.66
        self.activation_delay = 7
        
    def __repr__(self):
        return u"<Instance(%d,%s)>" % (self.id, self.key)
    
    def _get_key(self):
        return self._key
    
    def _set_key(self, value):
        self._key = value.lower()
    
    key = synonym('_key', descriptor=property(_get_key,
                                              _set_key))
    
    def _get_members(self):
        members = []
        for membership in self.memberships:
            if not membership.expire_time:
                members.append(membership.user)
        global_membership = model.Permission.by_code('global.member')
        for group in global_membership.groups:
            for membership in group.memberships:
                if membership.instance == None and not membership.expire_time:
                    members.append(membership.user)
        return members
    
    members = property(_get_members)
    
    @classmethod
    def find(cls, key, instance_filter=True, include_deleted=False):
        key = unicode(key.lower())
        try:
            q = meta.Session.query(Instance)
            q = q.filter(Instance.key==key)
            if not include_deleted:
                q = q.filter(or_(Instance.delete_time==None,
                                 Instance.delete_time>datetime.utcnow()))
            return q.one()
        except:
            log.exception("find(%s)" % id)
            return None
    
    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
               self.delete_time<=at_time
    
    def _index_id(self):
        return self.key
    
    @classmethod  
    def all(cls):
        return meta.Session.query(Instance).all()
