from datetime import datetime
import logging

from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func, or_ 
from sqlalchemy.orm import relation, backref

from meta import Base
import user 
import meta 

log = logging.getLogger(__name__)

class Twitter(Base):
    __tablename__ = 'twitter'
        
    id = Column(Integer, primary_key=True)
    
    create_time = Column(DateTime, default=datetime.utcnow)
    delete_time = Column(DateTime, nullable=True)
    
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relation(user.User, lazy=False, primaryjoin="Twitter.user_id==User.id", 
                    backref=backref('twitters', cascade='delete'))
    
    twitter_id = Column(Integer)
    key = Column(Unicode(255), nullable=False)
    secret = Column(Unicode(255), nullable=False)
    screen_name = Column(Unicode(255), nullable=False)
    priority = Column(Integer, default=4)
       
    def __init__(self, twitter_id, user, screen_name, key, secret):
        self.twitter_id = twitter_id
        self.user = user
        self.screen_name = screen_name
        self.key = key
        self.secret = secret
            
    def __repr__(self):
        return u"<Twitter(%d,%d,%s,%s)>" % (self.id,
                                            self.twitter_id, 
                                            self.user.user_name,
                                            self.screen_name)  
    
    @classmethod
    def find(cls, screen_name, include_deleted=False):
        try:
            q = meta.Session.query(Twitter)
            q = q.filter(Twitter.screen_name==screen_name)
            if not include_deleted:
                q = q.filter(or_(Twitter.delete_time==None,
                                 Twitter.delete_time>datetime.utcnow()))
            return q.one()
        except Exception, e:
            log.warn("find(%s): %s" % (screen_name, e))
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
        