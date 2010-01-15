from datetime import datetime
import logging

from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func
from sqlalchemy.orm import relation, backref

from meta import Base
import meta
import filter as ifilter

from user import User
from delegation import Delegation
from poll import Poll

log = logging.getLogger(__name__)

class Vote(Base):
    # REFACT: Not voted yet is expressed as None in varous places
    # Might be nice to have an explicit value for that
    YES = 1
    NO = -1
    ABSTAIN = 0
        
    __tablename__ = 'vote'
    
    id = Column(Integer, primary_key=True)
    orientation = Column(Integer, nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relation(User, 
        primaryjoin="Vote.user_id==User.id", 
        backref=backref('votes', cascade='delete', order_by='Vote.create_time.desc()'))
    
    poll_id = Column(Integer, ForeignKey('poll.id'), nullable=False)
    poll = relation(Poll, backref=backref('votes', order_by='Vote.create_time.desc()'))
    
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
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Vote)
            q = q.filter(Vote.id==int(id))
            vote = q.one()
            if ifilter.has_instance() and instance_filter:
                vote = vote.poll.proposal.instance == ifilter.get_instance() \
                        and vote or None
            return vote
        except:
            log.exception("find(%s)" % id) 
            return None
        
    def _index_id(self):
        return self.id

