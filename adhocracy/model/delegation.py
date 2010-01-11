from datetime import datetime

from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func, or_
from sqlalchemy.orm import relation, backref

import meta
import filter as ifilter
from meta import Base
from user import User
from delegateable import Delegateable

class Delegation(Base):
    __tablename__ = 'delegation'
    
    id = Column(Integer, primary_key=True)
    
    # REFACT: consider to rename this to target_user or target
    agent_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    agent = relation(User,
        primaryjoin="Delegation.agent_id == User.id", 
        backref=backref('agencies', cascade='all'))
    
    # REFACT: consider to rename this to source_user or source
    principal_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    principal = relation(User, 
        primaryjoin="Delegation.principal_id==User.id", 
        backref=backref('delegated', cascade='all'))
    
    scope_id = Column(Integer, ForeignKey('delegateable.id'), nullable=False)
    scope = relation(Delegateable, lazy=False,
        primaryjoin="Delegation.scope_id==Delegateable.id", 
        backref=backref('delegations', cascade='all'))
    
    create_time = Column(DateTime, default=datetime.utcnow)
    revoke_time = Column(DateTime, default=None, nullable=True)
    # can't be implicit by the next delegation being cast as multiple delegations at the same time are supported
    
    def __init__(self, principal, agent, scope):
        self.principal = principal
        self.agent = agent
        self.scope = scope
    
    def __repr__(self):
        return u"<Delegation(%s, %s->%s, %s)>" % (
            self.id, 
            self.principal.user_name, 
            self.agent.user_name,
            self.scope.id
        )
    
    def is_match(self, delegateable):
        if self.is_revoked():
            return False
        # TODO: this is a one-off of using permission in the model
        # rethink this. 
        if not self.principal.has_permission("vote.cast"):
            return False
        return self.scope == delegateable or self.scope.is_super(delegateable)
    
    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Delegation)
            q = q.filter(Delegation.id==id)
            if not include_deleted:
                q = q.filter(or_(Delegation.revoke_time==None,
                                 Delegation.revoke_time>datetime.utcnow()))
            d = q.one()
            if ifilter.has_instance() and instance_filter:
                if d.scope.instance != ifilter.get_instance():
                    return None 
            return d
        except:
            return None
        
    def revoke(self, revoke_time=None):
        if revoke_time is None:
            revoke_time = datetime.utcnow()
        if self.revoke_time is None:
            self.revoke_time = revoke_time
            
    def is_revoked(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.revoke_time is not None) and \
               self.revoke_time<=at_time
        
    def delete(self, delete_time=None):
        return self.revoke(revoke_time=delete_time)
    
    def is_deleted(self, at_time=None):
        return self.is_revoked(at_time=at_time)
    
    def _index_id(self):
        return self.id
    
    