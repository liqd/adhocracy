from datetime import datetime

from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func, or_
from sqlalchemy.orm import relation, backref

from meta import Base
import user
import meta

class Watch(Base):
    __tablename__ = 'watch'
        
    id = Column(Integer, primary_key=True)
    create_time = Column(DateTime, default=func.now())
    delete_time = Column(DateTime, nullable=True)
    
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relation(user.User, primaryjoin="Watch.user_id==User.id")
    
    entity_type = Column(Unicode(255), nullable=False, index=True)
    entity_ref = Column(Unicode(255), nullable=False, index=True)
    
    def __init__(self, user, entity_type, entity_ref):
        self.user = user
        self.entity_type = entity_type
        self.entity_ref = entity_ref
        
    def __repr__(self):
        return "<Watch(%s,%s,%s)>" % (self.id, self.user.user_name, self.entity_ref)
    
    @classmethod
    def by_id(cls, id, include_deleted=False):
        try:
            q = meta.Session.query(Watch)
            q = q.filter(Watch.id==id)
            if not include_deleted:
                q = q.filter(or_(Watch.delete_time==None,
                                 Watch.delete_time>datetime.now()))
            return q.one()
        except:
            return None
    
    @classmethod
    def find(cls, user, ref, include_deleted=False):
        try:
            q = meta.Session.query(Watch)
            q = q.filter(Watch.user==user)
            q = q.filter(Watch.entity_ref==ref)
            if not include_deleted:
                q = q.filter(or_(Watch.delete_time==None,
                                 Watch.delete_time>datetime.now()))
            return q.one()
        except:
            return None
        