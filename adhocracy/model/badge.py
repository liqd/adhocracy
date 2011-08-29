from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Boolean, Integer, DateTime, Unicode

from adhocracy.model import meta

log = logging.getLogger(__name__)


badge_table = Table(
    'badge', meta.data,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('title', Unicode(40), nullable=False),
    Column('color', Unicode(7), nullable=False),
    Column('description', Unicode(255), default=u'', nullable=False),
    Column('group_id', Integer, ForeignKey('group.id', ondelete="CASCADE")),
    Column('display_group', Boolean, default=False),
    Column('badge_delegateable', Boolean, default=False))


class Badge(object):

    def __init__(self, title, color, description, group=None,
                 display_group=False, badge_delegateable=False):
        self.title = title
        self.description = description
        self.color = color
        self.group = group
        self.display_group = display_group
        self.badge_delegateable = badge_delegateable

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
        q = meta.Session.query(Badge)
        try:
            q = q.filter(Badge.id == int(title))
        except ValueError:
            q = q.filter(Badge.title.like(title))
        return q.first()

    @classmethod
    def all(cls):
        q = meta.Session.query(Badge)
        return q.all()

    @classmethod
    def create(cls, title, color, description, group=None,
                 display_group=False, badge_delegateable=False):
        badge = cls(title, color, description, group, display_group,
                    badge_delegateable)
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
                    group=self.group and self.group.code or None,
                    display_group=self.display_group,
                    users=[user.name for user in self.users],
                    badge_delegateable=self.badge_delegateable)

    def _index_id(self):
        return self.id
                             
