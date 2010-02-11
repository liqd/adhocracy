from datetime import datetime
import logging

from sqlalchemy import Table, Column, Integer, UnicodeText, ForeignKey, DateTime, func

import meta

log = logging.getLogger(__name__)

revision_table = Table('revision', meta.data,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('text', UnicodeText(), nullable=False),
    Column('sentiment', Integer, default=0),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('comment_id', Integer, ForeignKey('comment.id'), nullable=False)
    )

class Revision(object):
    
    def __init__(self, comment, user, text):
        self.comment = comment
        self.user = user
        self.text = text
    
        
    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Revision)
            q = q.filter(Revision.id==id)
            return q.limit(1).first()
        except Exception, e: 
            log.warn("find(%s): %s" % (id, e))
            return None
    
        
    def to_dict(self):
        d = dict(id=self.id,
                 comment=self.comment_id,
                 create_time=self.create_time,
                 user=self.user.user_name,
                 text=self.text)
        return d
    
            
    def _index_id(self):
        return self.id
    
    
    def __repr__(self):
        return u"<Revision(%d,%s,%s)>" % (self.id, 
                                          self.user.user_name, 
                                          self.comment_id)
