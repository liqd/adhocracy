from sqlalchemy import Column, Integer, UnicodeText, ForeignKey, DateTime, func
from sqlalchemy.orm import relation, backref

import meta
from meta import Base
import user
import comment
from comment import Comment

class Revision(Base):
    __tablename__ = 'revision'
        
    id = Column(Integer, primary_key=True)
    create_time = Column(DateTime, default=func.now())
    text = Column(UnicodeText(), nullable=False)
    sentiment = Column(Integer, default=0)
    
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relation(user.User, lazy=True, primaryjoin="Revision.user_id==User.id", 
                    backref=backref('revisions'))
    
    comment_id = Column(Integer, ForeignKey('comment.id'), nullable=False)
       
    def __init__(self, comment, user, text):
        self.comment = comment
        self.user = user
        self.text = text
        
    def __repr__(self):
        return u"<Revision(%d,%s,%s)>" % (self.id, 
                                          self.user.user_name, 
                                          self.comment_id)
        
    @classmethod
    def find(cls, id, instance_filter=True):
        try:
            return meta.Session.query(Revision).filter(Revision.id==id).one()
        except: 
            return None
            
    def _index_id(self):
        return self.id
    

Revision.comment = relation(Comment, lazy=False,
                           backref=backref('revisions', cascade='all',
                                           lazy=True,
                                           order_by=Revision.create_time.desc()))
