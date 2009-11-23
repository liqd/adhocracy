from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func
from sqlalchemy.orm import relation, backref

from meta import Base
import user
import motion 

class Poll(Base):
    __tablename__ = 'poll'
        
    id = Column(Integer, primary_key=True)
    begin_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime, nullable=True)
    
    begin_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    begin_user = relation(user.User, 
                          primaryjoin="Poll.begin_user_id==User.id")
    
    end_user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    end_user = relation(user.User, 
                        primaryjoin="Poll.end_user_id==User.id")
    
    motion_id = Column(Unicode(10), ForeignKey('motion.id'), nullable=False)
       
    def __init__(self, motion, begin_user):
        self.motion = motion
        self.begin_user = begin_user
            
    def __repr__(self):
        return u"<Poll(%d,%s,%s,%s)>" % (self.id, 
                                         self.motion_id,
                                         self.begin_time, 
                                         self.end_time)  
    
    def _index_id(self):
        return self.id
    
    @classmethod
    def find(cls, id, instance_filter=True):
        try:
            q = meta.Session.query(Poll)
            q = q.filter(Poll.id==int(id))
            poll = q.one()
            if ifilter.has_instance() and instance_filter:
                poll = poll.motion.instance == ifilter.get_instance() \
                        and poll or None
            return poll
        except Exception: 
            return None

Poll.motion = relation(motion.Motion, backref=backref('polls', cascade='delete', 
                       lazy=False, order_by=Poll.begin_time.desc()))