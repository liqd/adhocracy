from datetime import datetime

from sqlalchemy import Table, Column, Integer, Unicode, ForeignKey, DateTime, func

import meta
from proposal import Proposal

dependency_table = Table('dependency', meta.data,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('proposal_id', Integer, ForeignKey('proposal.id'), nullable=False),
    Column('requirement_id', Integer, ForeignKey('proposal.id'), nullable=False)
    )

class Dependency(object):
    
    def __init__(self, proposal, requirement):
        if proposal == requirement:
            raise ValueError()
        self.proposal = proposal
        self.requirement = requirement
    
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
        return dict(proposal=self.proposal_id,
                    requirement=self.requirement_id,
                    create_time=self.create_time,
                    id=self.id)
    
    def __repr__(self):
        return "<Depdendency(%d,%d)>" % (self.proposal_id, self.requirement_id)
