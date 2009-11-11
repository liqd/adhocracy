from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import relation, backref

import meta
from meta import Base
import user
import delegateable

class Comment(Base):
    __tablename__ = 'comment'
        
    id = Column(Integer, primary_key=True)
    create_time = Column(DateTime, default=func.now())
    delete_time = Column(DateTime, default=None, nullable=True)
    
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    creator = relation(user.User, backref=backref('comments'))
    
    topic_id = Column(Unicode(10), ForeignKey('delegateable.id'), nullable=False)
    topic = relation(delegateable.Delegateable, backref=backref('comments', cascade='all'))
    
    canonical = Column(Boolean, default=False)
    
    reply_id = Column(Integer, ForeignKey('comment.id'), nullable=True)
    
    def __init__(self, topic, creator,):
        self.topic = topic
        self.creator = creator
        
    def __repr__(self):
        return "<Comment(%d,%s,%s,%s)>" % (self.id, self.creator.user_name,
                                          self.topic_id, self.create_time)
        
    def _get_latest(self):
        if not len(self.revisions):
            raise ValueError("No latest revision exists")
        return self.revisions[0]
    
    def _set_latest(self, rev):
        self.revisions.insert(0, rev)
        
    latest = property(_get_latest, _set_latest)

    @classmethod
    def find(cls, id, instance_filter=True):
        try:
            q = meta.Session.query(Comment)
            q = q.filter(Comment.id==id)
            return q.one()
        except: 
            return None
        
    def _index_id(self):
        return self.id
    

Comment.reply = relation(Comment, cascade='delete', 
                         remote_side=Comment.id, 
                         backref=backref('replies'))