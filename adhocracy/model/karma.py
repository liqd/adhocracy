from datetime import datetime

from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func
from sqlalchemy.orm import relation, backref

from meta import Base
import meta
import filter as ifilter

from instance import Instance
from user import User
from comment import Comment
from delegateable import Delegateable

class Karma(Base):
    __tablename__ = 'karma'
    
    id = Column(Integer, primary_key=True)
    value = Column(Integer, nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    
    comment_id = Column(Integer, ForeignKey('comment.id'), nullable=False)
    comment = relation(Comment, backref=backref('karmas', cascade='delete'))
    
    donor_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    donor = relation(User, primaryjoin="Karma.donor_id==User.id",
                     backref=backref('karma_given'))
    
    recipient_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    recipient = relation(User, primaryjoin="Karma.recipient_id==User.id",
                         backref=backref('karma_received'))
               
    def __init__(self, value, donor, recipient, comment):
        self.value = value
        self.donor = donor
        self.comment = comment
        self.recipient = recipient
        
    def __repr__(self):
        return "<Karma(%s,%s,%s,%s,%s)>" % (self.id, self.donor.user_name, 
                                            self.value, self.recipient.user_name,
                                            self.comment.id) 
    
    def _index_id(self):
        return self.id
