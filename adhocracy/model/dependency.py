from datetime import datetime

from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func
from sqlalchemy.orm import relation, backref

from meta import Base
from proposal import Proposal

class Dependency(Base):
    __tablename__ = "dependency"
    
    id = Column(Integer, primary_key=True)
    create_time = Column(DateTime, default=datetime.utcnow)
    delete_time = Column(DateTime, nullable=True)
    
    proposal_id = Column(Integer, ForeignKey('proposal.id'), nullable=False)
    requirement_id = Column(Integer, ForeignKey('proposal.id'), nullable=False)
    
    def __init__(self, proposal, requirement):
        if proposal == requirement:
            raise ValueError()
        self.proposal = proposal
        self.requirement = requirement
    
    def __repr__(self):
        return "<Depdendency(%d,%d)>" % (self.proposal_id, self.requirement_id)
    
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
    
Dependency.proposal = relation(Proposal, primaryjoin="Dependency.proposal_id==Proposal.id", 
                             foreign_keys=[Dependency.proposal_id], 
                             backref=backref('dependencies', cascade='all'))

Dependency.requirement = relation(Proposal, primaryjoin="Dependency.requirement_id==Proposal.id", 
                                  foreign_keys=[Dependency.requirement_id], 
                                  backref=backref('dependents', cascade='all'))