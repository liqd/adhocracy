from datetime import datetime

from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func
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
    

Alternative.left = relation(Proposal, primaryjoin="Alternative.left_id==Proposal.id", 
                         foreign_keys=[Alternative.left_id], 
                         backref=backref('left_alternatives', cascade='all'))
Alternative.right = relation(Proposal, primaryjoin="Alternative.right_id==Proposal.id", 
                          foreign_keys=[Alternative.right_id], 
                          backref=backref('right_alternatives', cascade='all'))