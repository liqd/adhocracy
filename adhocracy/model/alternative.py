from datetime import datetime

from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func, or_
from sqlalchemy.orm import relation, backref

from meta import Base
from proposal import Proposal

class Alternative(Base):
    __tablename__ = "alternative"
    
    id = Column(Integer, primary_key=True)
    create_time = Column(DateTime, default=datetime.utcnow)
    delete_time = Column(DateTime, nullable=True)
    
    left_id = Column(Integer, ForeignKey('proposal.id'), nullable=False)
    right_id = Column(Integer, ForeignKey('proposal.id'), nullable=False)
    
    def __init__(self, left, right):
        if left == right:
            raise ValueError()
        (left, right) = sorted([left, right], key=lambda m: m.id)
        self.left = left
        self.right = right
    
    def __repr__(self):
        return "<Alternative(%d,%d)>" % (self.left_id, self.right_id)
    
    def other(self, this):
        return self.left if this==self.right else self.right
    
    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        if not self.is_deleted(delete_time):
            self.delete_time = delete_time
            
    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
               self.delete_time<=at_time
               
    def to_dict(self):
        return dict(left=self.left_id,
                    right=self.right_id,
                    create_time=self.create_time,
                    id=self.id)
    

Alternative.left = relation(Proposal, primaryjoin="Alternative.left_id==Proposal.id", 
                         foreign_keys=[Alternative.left_id], 
                         backref=backref('left_alternatives', cascade='all'))
Alternative.right = relation(Proposal, primaryjoin="Alternative.right_id==Proposal.id", 
                          foreign_keys=[Alternative.right_id], 
                          backref=backref('right_alternatives', cascade='all'))
