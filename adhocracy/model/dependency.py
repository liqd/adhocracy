from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func
from sqlalchemy.orm import relation, backref

from meta import Base
from motion import Motion

class Dependency(Base):
    __tablename__ = "dependency"
    
    id = Column(Integer, primary_key=True)
    create_time = Column(DateTime, default=func.now())
    delete_time = Column(DateTime, nullable=True)
    
    motion_id = Column(Unicode(10), ForeignKey('motion.id'), nullable=False)
    requirement_id = Column(Unicode(10), ForeignKey('motion.id'), nullable=False)
    
    def __init__(self, motion, requirement):
        if motion == requirement:
            raise ValueError()
        self.motion = motion
        self.requirement = requirement
    
    def __repr__(self):
        return "<Depdendency(%s,%s)>" % (self.motion_id, self.requirement_id)
    
Dependency.motion = relation(Motion, primaryjoin="Dependency.motion_id==Motion.id", 
                             foreign_keys=[Dependency.motion_id], 
                             backref=backref('dependencies', cascade='all'))

Dependency.requirement = relation(Motion, primaryjoin="Dependency.requirement_id==Motion.id", 
                                  foreign_keys=[Dependency.requirement_id], 
                                  backref=backref('dependents', cascade='all'))