from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Integer, DateTime

from adhocracy.model import meta
from adhocracy.model.badge import Badge

log = logging.getLogger(__name__)


user_badges_table = Table(
    'user_badges', meta.data,
    Column('id', Integer, primary_key=True),
    Column('badge_id', Integer, ForeignKey('badge.id'),
           nullable=False),
    Column('user_id', Integer, ForeignKey('user.id'),
           nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False))


class UserBadge(object):

    def __init__(self, user, badge, creator):
        self.user = user
        self.badge = badge
        self.creator = creator

    def __repr__(self):
        badge = self.badge.name.encode('ascii', 'replace')
        return "<userbadges(%s, badge %s/%s for user%s/%s)>" % (
            self.id, self.user.id, self.user.name, self.badge.id, badge)

    def delete(self):
        meta.Session.delete(self)
        meta.Session.flush()

    @classmethod
    def find(cls, id):
        q = meta.Session.query(UserBadge)
        q = q.filter(UserBadge.id == id)
        return q.limit(1).first()

    @classmethod
    def create(cls, user, badge, creator):
        assert isinstance(badge, Badge), (
            "badge has to be an :class:`adhocracy.model.badge.Badge`")
        userbadge = cls(user, badge, creator)
        meta.Session.add(userbadge)
        meta.Session.flush()
        return userbadge

    def _index_id(self):
        return self.id
