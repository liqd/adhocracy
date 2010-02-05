from datetime import datetime

import logging

from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func, or_ 
from sqlalchemy.orm import relation, backref

from meta import Base
import user 
import meta 

log = logging.getLogger(__name__)

class OpenID(Base):
    __tablename__ = 'openid'
        
    id = Column(Integer, primary_key=True)
    create_time = Column(DateTime, default=datetime.utcnow)
    delete_time = Column(DateTime, nullable=True)
    
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relation(user.User, lazy=False, primaryjoin="OpenID.user_id==User.id", 
                    backref=backref('openids', cascade='delete'))
    
    identifier = Column(Unicode(255), nullable=False, index=True)
       
    def __init__(self, identifier, user):
        self.identifier = identifier
        self.user = user
            
    def __repr__(self):
        return u"<OpenID(%d,%s,%s)>" % (self.id, 
                                        self.identifier,
                                        self.user.user_name)  
    
    @classmethod
    def find(cls, identifier, include_deleted=False):
        try:
            q = meta.Session.query(OpenID)
            q = q.filter(OpenID.identifier==identifier)
            if not include_deleted:
                q = q.filter(or_(OpenID.delete_time==None,
                                 OpenID.delete_time>datetime.utcnow()))
            return q.one()
        except Exception, e:
            log.warn("find(%s): %s" % (identifier, e))
            return None
        
    
    @classmethod
    def by_id(cls, id, include_deleted=False):
        try:
            q = meta.Session.query(OpenID)
            q = q.filter(OpenID.id==id)
            if not include_deleted:
                q = q.filter(or_(OpenID.delete_time==None,
                                 OpenID.delete_time>datetime.utcnow()))
            return q.one()
        except Exception:
            log.exception("by_id(%s)" % id)
            return None
            
    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        if self.delete_time is None:
            self.delete_time = delete_time  
    
    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
            self.delete_time <= at_time