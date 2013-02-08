from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey, or_
from sqlalchemy import DateTime, Integer, Unicode

import meta

log = logging.getLogger(__name__)


twitter_table = Table(
    'twitter', meta.data,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('twitter_id', Integer),
    Column('key', Unicode(255), nullable=False),
    Column('secret', Unicode(255), nullable=False),
    Column('screen_name', Unicode(255), nullable=False),
    Column('priority', Integer, default=4)
)


class Twitter(object):

    def __init__(self, twitter_id, user, screen_name, key, secret):
        self.twitter_id = twitter_id
        self.user = user
        self.screen_name = screen_name
        self.key = key
        self.secret = secret

    @classmethod
    def find(cls, screen_name, include_deleted=False):
        try:
            q = meta.Session.query(Twitter)
            q = q.filter(Twitter.screen_name == screen_name)
            if not include_deleted:
                q = q.filter(or_(Twitter.delete_time == None,
                                 Twitter.delete_time > datetime.utcnow()))
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

    def __repr__(self):
        return u"<Twitter(%d,%d,%s,%s)>" % (self.id,
                                            self.twitter_id,
                                            self.user.user_name,
                                            self.screen_name)
