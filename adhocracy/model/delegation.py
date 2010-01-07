from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func
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
    
    create_time = Column(DateTime, default=func.now())
    revoke_time = Column(DateTime, default=None, nullable=True)
    # can't be implicit by the next delegation being cast as multiple delegations at the same time are supported
    
    def __init__(self, principal, agent, scope):
        self.principal = principal
        self.agent = agent
        self.scope = scope
        
    def __repr__(self):
        return u"<Delegation(%s,%s->%s,%s)>" % (self.id, 
            self.principal.user_name, 
            self.agent.user_name,
            self.scope.id)
            
    def is_match(self, delegateable):
        if self.revoke_time:
            return False
        if not self.principal.has_permission("vote.cast"):
            return False
        return self.scope == delegateable or self.scope.is_super(delegateable)
       
    @classmethod
    def find(cls, id, instance_filter=True):
        try:
            q = meta.Session.query(Delegation)
            q = q.filter(Delegation.id==id)
            d = q.one()
            if ifilter.has_instance() and instance_filter:
                if d.scope.instance != ifilter.get_instance():
                    return None 
            return d
        except Exception: 
            return None
            
    def _index_id(self):
        return self.id
    
    