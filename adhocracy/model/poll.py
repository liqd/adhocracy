from datetime import datetime

from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func
from sqlalchemy.orm import relation, backref

# REFACT: use absolute imports to make it easier to see where what comes from
from meta import Base
import user
import meta
import filter as ifilter
import proposal 

class Poll(Base):
    __tablename__ = 'poll'
    
    id = Column(Integer, primary_key=True)
    begin_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    
    begin_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    begin_user = relation(user.User, 
                          primaryjoin="Poll.begin_user_id==User.id")
    
    end_user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    end_user = relation(user.User, 
                        primaryjoin="Poll.end_user_id==User.id")
    
    proposal_id = Column(Integer, ForeignKey('proposal.id'), nullable=False)
    
    def __init__(self, proposal, begin_user):
        self.proposal = proposal
        self.begin_user = begin_user
    
    def __repr__(self):
        return u"<Poll(%s,%s,%s,%s)>" % (self.id, 
                                         self.proposal_id,
                                         self.begin_time, 
                                         self.end_time)
    
    def _index_id(self):
        return self.id
    
    def end_poll_with_user(self, a_user):
        self.end_time = datetime.utcnow()
        self.end_user = a_user
    
    @classmethod
    def find(cls, id, instance_filter=True):
        try:
            q = meta.Session.query(Poll)
            q = q.filter(Poll.id==int(id))
            poll = q.one()
            if ifilter.has_instance() and instance_filter:
                poll = poll.proposal.instance == ifilter.get_instance() \
                        and poll or None
            return poll
        except Exception:
            return None
    

Poll.proposal = relation(proposal.Proposal, backref=backref('polls', cascade='all',
                       lazy=False, order_by=Poll.begin_time.desc()))