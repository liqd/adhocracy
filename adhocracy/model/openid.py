from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func
from sqlalchemy.orm import relation, backref

from meta import Base
import user 
import meta 

class OpenID(Base):
    __tablename__ = 'openid'
        
    id = Column(Integer, primary_key=True)
    create_time = Column(DateTime, default=func.now())
    
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relation(user.User, lazy=False, primaryjoin="OpenID.user_id==User.id", 
                    backref=backref('openid', cascade='delete'))
    
    identifier = Column(Unicode(255), nullable=False, index=True)
       
    def __init__(self, identifier, user):
        self.identifier = identifier
        self.user = user
            
    def __repr__(self):
        return u"<OpenID(%d,%s,%s)>" % (self.id, 
                                        self.identifier,
                                        self.user.user_name)  
    
    @classmethod
    def find(cls, identifier):
        try:
            q = meta.Session.query(OpenID)
            q = q.filter(OpenID.identifier==identifier)
            return q.one()
        except Exception, e:
            print e 
            return None