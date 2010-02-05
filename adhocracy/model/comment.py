from datetime import datetime
import logging

from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, Boolean, func, or_
from sqlalchemy.orm import relation, backref

import meta
from meta import Base
import user
import delegateable

log = logging.getLogger(__name__)

class Comment(Base):
    __tablename__ = 'comment'
        
    id = Column(Integer, primary_key=True)
    create_time = Column(DateTime, default=datetime.utcnow)
    delete_time = Column(DateTime, default=None, nullable=True)
    
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    creator = relation(user.User, lazy=False, backref=backref('comments'))
    
    topic_id = Column(Integer, ForeignKey('delegateable.id'), nullable=False)
    topic = relation(delegateable.Delegateable, backref=backref('comments', cascade='all'))
    
    canonical = Column(Boolean, default=False)
    
    reply_id = Column(Integer, ForeignKey('comment.id'), nullable=True)
    
    def __init__(self, topic, creator):
        self.topic = topic
        self.creator = creator
        
    def __repr__(self):
        return "<Comment(%d,%s,%d,%s)>" % (self.id, self.creator.user_name,
                                          self.topic_id, self.create_time)
    
    def _get_latest(self):
        return self.revisions[0]
    
    def _set_latest(self, latest):
        self.revisions.append(latest)
    
    latest = property(_get_latest, _set_latest)
    
    def root(self):
        return self.reply.root() if self.reply else self
    
    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Comment)
            q = q.filter(Comment.id==id)
            if not include_deleted:
                q = q.filter(or_(Comment.delete_time==None,
                                 Comment.delete_time>datetime.utcnow()))
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e)) 
            return None
    
    @classmethod    
    def create(cls, text, user, topic, reply=None, canonical=False):
        from karma import Karma
        comment = Comment(topic, user)
        comment.canonical = canonical
        comment.reply = reply
        karma = Karma(1, user, user, comment)
        meta.Session.add(comment)
        meta.Session.add(karma)
        comment.create_revision(text, user)
        return comment
    
    def create_revision(self, text, user):
        from revision import Revision
        import adhocracy.lib.text as libtext
        rev = Revision(self, user, 
                       libtext.cleanup(text))
        meta.Session.add(rev)
        self.latest = rev
        meta.Session.flush()
        return rev
        
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
                    
    def _index_id(self):
        return self.id
        
    def to_dict(self):
        d = dict(id=self.id,
                 create_time=self.create_time,
                 topic=self.topic_id,
                 creator=self.creator.user_name)
        if self.reply_id: 
            d['reply'] = self.reply_id
        if self.canonical:
            d['canonical'] = self.canonical
        if self.latest:
            d['latest'] = self.latest.to_dict()
        d['revisions'] = map(lambda r: r.id, self.revisions)
        return d
    

Comment.reply = relation(Comment, cascade='delete', 
                         remote_side=Comment.id, 
                         backref=backref('replies', lazy=False))