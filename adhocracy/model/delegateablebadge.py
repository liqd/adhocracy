from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Integer, DateTime

from adhocracy.model import meta
from adhocracy.model.badge import Badge
from adhocracy.model.delegateable import Delegateable

log = logging.getLogger(__name__)


delegateable_badge_table = Table(
    'delegateable_badges', meta.data,
    Column('id', Integer, primary_key=True),
    Column('badge_id', Integer, ForeignKey('badge.id'),
           nullable=False),
    Column('delegateable_id', Integer, ForeignKey('delegateable.id'),
           nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False))


class DelegateableBadge(object):

    def __init__(self, delegateable, badge, creator):
        self.delegateable = delegateable
        self.badge = badge
        self.creator = creator

    def __repr__(self):
        badge = self.badge.title.encode('ascii', 'replace')
        return "<delegateablebadges(%s, badge %s/%s for delegateable%s)>" % (
            self.id, self.badge.id, badge, self.delegateable.id)

    def delete(self):
        meta.Session.delete(self)
        meta.Session.flush()

    @classmethod
    def find(cls, id):
        q = meta.Session.query(DelegateableBadge)
        q = q.filter(DelegateableBadge.id == id)
        return q.limit(1).first()

    @classmethod
    def create(cls, delegateable, badge, creator):
        assert isinstance(badge, Badge), (
            "badge has to be an :class:`adhocracy.model.badge.Badge`")
        assert isinstance(delegateable, Delegateable), (
            "delegateable has to be an :class:`adhocracy.model.delegateable.Delegateable`") 
        delegateablebadge = cls(delegateable, badge, creator)
        meta.Session.add(delegateablebadge)
        meta.Session.flush()
        return delegateablebadge

    def _index_id(self):
        return self.id
