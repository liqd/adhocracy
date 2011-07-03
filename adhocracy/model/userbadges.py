from datetime import datetime
import logging

from sqlalchemy import Table, Column, Integer, ForeignKey, DateTime, Unicode

from adhocracy.model import meta

log = logging.getLogger(__name__)


badge_table = Table(
    'badge', meta.data,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('title', Unicode(40), nullable=False),
    Column('color', Unicode(7), nullable=False),
    Column('group', Integer, ForeignKey('group.id', ondelete="CASCADE")))


user_badges_table = Table('user_badges', meta.data,
    Column('id', Integer, primary_key=True),
    Column('badge_id', Integer, ForeignKey('badge.id'),
           nullable=False),
    Column('user_id', Integer, ForeignKey('user.id'),
           nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False))


class Badge(object):

    def __init__(self, title, color):
        self.title = title
        self.color = color

    def __repr__(self):
        return "<Badge(%s,%s)>" % (self.id,
                                   self.title.encode('ascii', 'replace'))

    def __unicode__(self):
        return self.title

    def count(self):
        if self._count is None:
            from badges import Badges
            q = meta.Session.query(Badges)
            q = q.filter(Badges.badge == self)
            self._count = q.count()
        return self._count

    def __le__(self, other):
        return self.title >= other.title

    def __lt__(self, other):
        return self.title > other.title

    @classmethod
    def by_id(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Badge)
            q = q.filter(Badge.id == id)
            return q.limit(1).first()
        except Exception, e:
            log.warn("by_id(%s): %s" % (id, e))
            return None

    @classmethod
    def find(cls, title):
        q = meta.Session.query(Badge).filter(Badge.title.like(title))
        return q.first()

    @classmethod
    def all(cls):
        q = meta.Session.query(Badge)
        return q.all()

    @classmethod
    def create(cls, title, color):
        badge = cls(title, color)
        meta.Session.add(badge)
        meta.Session.flush()
        return badge

    @classmethod
    def find_or_create(cls, title):
        badge = cls.find(title)
        if badge is None:
            badge = cls.create(title)
        return badge

    def to_dict(self):
        return dict(id=self.id,
                    title=self.title,
                    color=self.color,
                    users=[user.name for user in self.users])

    def _index_id(self):
        return self.id


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
