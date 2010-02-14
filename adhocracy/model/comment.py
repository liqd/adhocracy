from datetime import datetime
import logging

from sqlalchemy import Table, Column, Integer, Unicode, ForeignKey, DateTime, Boolean, func, or_
from sqlalchemy.orm import relation, backref

import meta


log = logging.getLogger(__name__)


comment_table = Table('comment', meta.data,                  
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, default=None, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('topic_id', Integer, ForeignKey('delegateable.id'), nullable=False),
    Column('canonical', Boolean, default=False),
    Column('reply_id', Integer, ForeignKey('comment.id'), nullable=True),
    Column('poll_id', Integer, ForeignKey('poll.id'), nullable=True)
    )
     


class Comment(object):
    
    def __init__(self, topic, creator):
        self.topic = topic
        self.creator = creator
    
    def root(self):
        return self if self.reply is None else self.reply.root()
    
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
    def create(cls, text, user, topic, reply=None, canonical=False, with_vote=False):
        from poll import Poll
        comment = Comment(topic, user)
        comment.canonical = canonical
        comment.reply = reply
        meta.Session.add(comment)
        meta.Session.flush()
        poll = Poll.create(topic, user, Poll.RATE, comment,
                           with_vote=with_vote)
        comment.poll = poll
        comment.create_revision(text, user)
        return comment
    
    
    def create_revision(self, text, user):
        from revision import Revision
        from adhocracy.lib.text import cleanup
        rev = Revision(self, user, cleanup(text))
        meta.Session.add(rev)
        self.revisions.append(rev)
        meta.Session.flush()
        return rev
    
        
    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        if not self.is_deleted(delete_time):
            self.delete_time = delete_time
            if self.poll is not None:
                self.poll.end()
    
    
    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
               self.delete_time<=at_time
               
               
    def is_edited(self):
        if self.is_deleted():
            return False
        return self.latest.create_time != self.create_time
    
    
    def is_mutable(self):
        return (not self.canonical) or self.topic.is_mutable()
        
                    
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
    
    
    def __repr__(self):
        return "<Comment(%d,%s,%d,%s)>" % (self.id, self.creator.user_name,
                                          self.topic_id, self.create_time)
