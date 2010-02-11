from datetime import datetime
import logging

from sqlalchemy import Table, Column, Integer, Unicode, ForeignKey, DateTime, func

import meta
import filter as ifilter

from instance import Instance
from user import User
from comment import Comment
from delegateable import Delegateable

log = logging.getLogger(__name__)


karma_table = Table('karma', meta.data,
    Column('id', Integer, primary_key=True),
    Column('value', Integer, nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('comment_id', Integer, ForeignKey('comment.id'), nullable=False),
    Column('donor_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('recipient_id', Integer, ForeignKey('user.id'), nullable=False)     
    )


class Karma(object):
               
    def __init__(self, value, donor, recipient, comment):
        self.value = value
        self.donor = donor
        self.comment = comment
        self.recipient = recipient
    
    @classmethod
    def find_by_user_and_comment(cls, user, comment):
        try:
            q = meta.Session.query(Karma)
            q = q.filter(Karma.comment==comment)
            q = q.filter(Karma.donor==user)
            return q.limit(1).first()
        except Exception, e: 
            log.warn("find(%s:%s): %s" % (user.user_name, comment.id, e))
            return None
    
    def _index_id(self):
        return self.id
      
    def __repr__(self):
        return "<Karma(%s,%s,%s,%s,%s)>" % (self.id, self.donor.user_name, 
                                            self.value, self.recipient.user_name,
                                            self.comment.id) 
