from datetime import datetime

from sqlalchemy import Table, Column, Integer, Unicode, ForeignKey, DateTime, func, or_
from sqlalchemy.orm import relation, backref

import meta
from proposal import Proposal

alternative_table = Table('alternative', meta.data, 
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('left_id', Integer, ForeignKey('proposal.id'), nullable=False),
    Column('right_id', Integer, ForeignKey('proposal.id'), nullable=False)
    )

class Alternative(object):
    
    def __init__(self, left, right):
        if left == right:
            raise ValueError()
        (left, right) = sorted([left, right], key=lambda m: m.id)
        self.left = left
        self.right = right
    
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
    
    def __repr__(self):
        return "<Alternative(%d,%d)>" % (self.left_id, self.right_id)
