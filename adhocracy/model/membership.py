from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, DateTime, func, Boolean
from sqlalchemy.orm import relation, backref

import filter as ifilter
from meta import Base
import user

class Membership(Base):
    __tablename__ = 'membership'
    
    id = Column(Integer, primary_key=True)
    approved = Column(Boolean, nullable=True)
    
    create_time = Column(DateTime, default=datetime.utcnow)
    expire_time = Column(DateTime, nullable=True)
    access_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relation(user.User, lazy=False, 
        primaryjoin="Membership.user_id==User.id", 
        backref=backref('memberships', lazy=True))
    
    instance_id = Column(Integer, ForeignKey('instance.id'), nullable=True)
    instance = relation('Instance', backref=backref('memberships'), lazy=True)
    
    group_id = Column(Integer, ForeignKey('group.id'), nullable=False)
    group = relation('Group', backref=backref('memberships'), lazy=False)
    
    def __init__(self, user, instance, group, approved=True):
        self.user = user
        self.instance = instance
        self.group = group
        self.approved = approved
        
    def expire(self, expire_time=None):
        if expire_time is None:
            expire_time = datetime.utcnow()
        if not self.is_expired(at_time=expire_time):
            self.expire_time = expire_time
        
    def is_expired(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.expire_time is not None) and \
               self.expire_time<=at_time
    
    def delete(self, delete_time=None):
        return self.expire(expire_time=delete_time)
        
    def is_deleted(self, at_time=None):
        return self.is_expired(at_time=at_time)
        
    def __repr__(self):
        return u"<Membership(%d,%s,%s,%s)>" % (self.id, 
                                               self.user.user_name,
                                               self.instance and self.instance.key or "",
                                               self.group.code)