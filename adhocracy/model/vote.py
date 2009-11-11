from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func
from sqlalchemy.orm import relation, backref

from meta import Base
import meta
import filter as ifilter

from user import User
from delegation import Delegation
from poll import Poll

class Vote(Base):
    AYE = 1
    NAY = -1
    ABSTAIN = 0
        
    __tablename__ = 'vote'
    
    id = Column(Integer, primary_key=True)
    orientation = Column(Integer, nullable=False)
    create_time = Column(DateTime, default=func.now())
    
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    # user See below 
    
    poll_id = Column(Integer, ForeignKey('poll.id'), nullable=False)
    # motion See below
    
    delegation_id = Column(Integer, ForeignKey('delegation.id'), nullable=True)
    delegation = relation(Delegation, 
        primaryjoin="Vote.delegation_id==Delegation.id", 
        backref=backref('votes', cascade='delete'))
    
    def __init__(self, user, poll, orientation, delegation=None):
        self.user = user
        self.poll = poll
        self.orientation = orientation
        self.delegation = delegation
        
    def __repr__(self):
        return "<Vote(%s,%s,%s,%s,%s)>" % (self.id, 
            self.user.user_name,
            self.poll.id, 
            self.orientation,
            self.delegation.id if self.delegation else "DIRECT")
        
    @classmethod
    def find(cls, id, instance_filter=True):
        try:
            q = meta.Session.query(Vote)
            q = q.filter(Vote.id==int(id))
            vote = q.one()
            if ifilter.has_instance() and instance_filter:
                vote = vote.poll.motion.instance == ifilter.get_instance() \
                        and vote or None
            return vote
        except Exception, e: 
            return None
        
    def _index_id(self):
        return self.id

Vote.user = relation(User, 
    primaryjoin="Vote.user_id==User.id", 
    backref=backref('votes', cascade='delete', order_by=Vote.create_time.desc()))

Vote.poll = relation(Poll, 
    backref=backref('votes', order_by=Vote.create_time.desc()))