from datetime import datetime
import logging

from sqlalchemy import Table, Column, Integer, ForeignKey, DateTime

import meta
import instance_filter as ifilter


log = logging.getLogger(__name__)


vote_table = Table(
    'vote', meta.data,
    Column('id', Integer, primary_key=True),
    Column('orientation', Integer, nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('poll_id', Integer, ForeignKey('poll.id'), nullable=False),
    Column('delegation_id', Integer, ForeignKey('delegation.id'),
           nullable=True)
)


class Vote(object):
    # REFACT: Not voted yet is expressed as None in varous places
    # Might be nice to have an explicit value for that
    YES = 1L
    NO = -1L
    ABSTAIN = 0L

    def __init__(self, user, poll, orientation, delegation=None):
        self.user = user
        self.poll = poll
        self.orientation = orientation
        self.delegation = delegation

    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Vote)
            q = q.filter(Vote.id == int(id))
            vote = q.first()
            if ifilter.has_instance() and instance_filter:
                vote = vote.poll.scope.instance == ifilter.get_instance() \
                    and vote or None
            return vote
        except Exception, e:
            log.exception(e)
            #log.warn("find(%s): %s" % (id, e))
            return None

    @classmethod
    def all_q(cls):
        return meta.Session.query(Vote)

    @classmethod
    def all(cls):
        return cls.all_q().all()

    def to_dict(self):
        return dict(id=self.id,
                    user=self.user_id,
                    poll=self.poll_id,
                    result=self.orientation,
                    create_time=self.create_time,
                    delegation=self.delegation_id)

    def __repr__(self):
        return "<Vote(%s,%s,%s,%s,%s)>" % (
            self.id,
            self.user.user_name,
            self.poll.id,
            self.orientation,
            self.delegation.id if self.delegation else "DIRECT")
