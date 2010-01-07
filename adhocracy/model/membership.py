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
    
    #def _get_context_group(self):
    #    if not self.instance or self.instance == ifilter.get_instance():
    #        return self.group

    #context_group = property(_get_context_group)
        
    def __init__(self, user, instance, group, approved=True):
        self.user = user
        self.instance = instance
        self.group = group
        self.approved = approved
        
    def __repr__(self):
        return u"<Membership(%d,%s,%s,%s)>" % (self.id, 
                                               self.user.user_name,
                                               self.instance and self.instance.key or "",
                                               self.group.code)