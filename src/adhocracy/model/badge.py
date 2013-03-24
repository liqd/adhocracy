'''
Badges for different uses (users, delegateables, categories
of delegateables). Badges use single table inheritance.
'''

from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Boolean, Integer, DateTime, String, Unicode

from adhocracy.model import meta, instance_filter as ifilter

log = logging.getLogger(__name__)
MARKER = object()


badge_table = Table(
    'badge', meta.data,
    #common attributes
    Column('id', Integer, primary_key=True),
    Column('type', String(40), nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('title', Unicode(40), nullable=False),
    Column('color', Unicode(7), nullable=False),
    Column('description', Unicode(255), default=u'', nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id',
                                              ondelete="CASCADE",),
           nullable=True),
    # attributes for hierarchical badges (CategoryBadges)
    Column('select_child_description', Unicode(255), default=u'',
           nullable=False),
    Column('parent_id', Integer, ForeignKey('badge.id', ondelete="CASCADE"),
           nullable=True),
    # attributes for UserBadges
    Column('group_id', Integer, ForeignKey('group.id', ondelete="CASCADE")),
    Column('display_group', Boolean, default=False),
    Column('visible', Boolean, default=True),
)


# --[ relation tables ]-----------------------------------------------------

instance_badges_table = Table(
    'instance_badges', meta.data,
    Column('id', Integer, primary_key=True),
    Column('badge_id', Integer, ForeignKey('badge.id'),
           nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'),
           nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False))


delegateable_badges_table = Table(
    'delegateable_badges', meta.data,
    Column('id', Integer, primary_key=True),
    Column('badge_id', Integer, ForeignKey('badge.id'),
           nullable=False),
    Column('delegateable_id', Integer, ForeignKey('delegateable.id'),
           nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False))


user_badges_table = Table(
    'user_badges', meta.data,
    Column('id', Integer, primary_key=True),
    Column('badge_id', Integer, ForeignKey('badge.id'),
           nullable=False),
    Column('user_id', Integer, ForeignKey('user.id'),
           nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False))


# --[ Badge base classes ]--------------------------------------------------


class Badge(object):

    def __init__(self, title, color, visible, description, instance=None):
        self.title = title
        self.description = description
        self.color = color
        self.visible = visible
        self.instance = instance

    @classmethod
    def create(cls, title, color, visible, description, instance=None):
        badge = cls(title, color, visible, description, instance)
        meta.Session.add(badge)
        meta.Session.flush()
        return badge

    def __repr__(self):
        return "<%s(%s,%s)>" % (self.__class__.__name__, self.id,
                                self.title.encode('ascii', 'replace'))

    def __unicode__(self):
        return self.title

    @classmethod
    def count(cls):
        return meta.Session.query(cls).count()

    def __le__(self, other):
        return self.title >= other.title

    def __lt__(self, other):
        return self.title > other.title

    @classmethod
    def by_id(cls, id, instance_filter=True):
        try:
            q = meta.Session.query(cls)
            q = q.filter(cls.id == id)
            if ifilter.has_instance() and instance_filter:
                q = q.filter((cls.instance_id ==
                              ifilter.get_instance().id))
            return q.limit(1).first()
        except Exception, e:
            log.warn("by_id(%s): %s" % (id, e))
            return None

    @classmethod
    def find(cls, title_or_id):
        q = meta.Session.query(cls)
        try:
            q = q.filter(cls.id == int(title_or_id))
        except ValueError:
            q = q.filter(cls.title.like(title_or_id))
        return q.first()

    @classmethod
    def findall_by_ids(cls, ids):
        if len(ids) == 0:
            return []
        q = meta.Session.query(cls)
        q = q.filter(cls.id.in_(ids))
        return q.all()

    @classmethod
    def all_q(cls, instance=MARKER):
        '''
        A preconfigured query for all Badges ordered by title.
        If *instance* is not given all badges are given.
        If *instance* is given (either `None` or an instance object),
        only these badges are returned.
        '''
        q = meta.Session.query(cls)
        if instance is not MARKER:
            q = q.filter(cls.instance == instance)
        return q

    @classmethod
    def all(cls, instance=None, include_global=False):
        """
        Return all badges, orderd by title.
        Without instance it only returns badges not bound to an instance.
        With instance it only returns badges bound to that instance.
        With instance and include_global it returns both badges bound to that
        instance and badges not bound to an instance.
        """
        q = cls.all_q(instance=instance)
        if include_global and instance is not None:
            q = q.union(cls.all_q(instance=None))
        return q.order_by(cls.title).all()

    def to_dict(self):
        return dict(id=self.id,
                    title=self.title,
                    color=self.color,
                    visible=self.visible,
                    description=self.description,
                    instance=self.instance.id if self.instance else None)


class Badges(object):
    '''Base class for entity<->Badge relations'''

    def delete(self):
        meta.Session.delete(self)
        meta.Session.flush()

    @classmethod
    def find(cls, id):
        q = meta.Session.query(cls)
        q = q.filter(cls.id == id)
        return q.limit(1).first()


# --[ User Badges ]---------------------------------------------------------

class UserBadge(Badge):

    polymorphic_identity = 'user'

    @classmethod
    def create(cls, title, color, visible, description, group=None,
               display_group=False, instance=None):
        badge = cls(title, color, visible, description, instance)
        badge.group = group
        badge.display_group = display_group
        meta.Session.add(badge)
        meta.Session.flush()
        return badge

    def assign(self, user, creator):
        UserBadges.create(user, self, creator)
        meta.Session.refresh(user)
        meta.Session.refresh(self)

    def to_dict(self):
        d = super(UserBadge, self).to_dict()
        d['group'] = self.group.code if self.group else None,
        d['users'] = [user.name for user in self.users]
        return d


class UserBadges(Badges):

    def __init__(self, user, badge, creator):
        self.user = user
        self.badge = badge
        self.creator = creator

    def __repr__(self):
        title = self.badge.title.encode('ascii', 'replace')
        return "<userbadges(%s, badge %s/%s for user%s/%s)>" % (
            self.id, self.badge.id, title, self.user.id, self.user.name)

    @classmethod
    def create(cls, user, badge, creator):
        assert isinstance(badge, Badge), (
            "badge has to be an :class:`adhocracy.model.badge.Badge`")
        userbadge = cls(user, badge, creator)
        meta.Session.add(userbadge)
        meta.Session.flush()
        return userbadge


# --[ Instance Badges ]-------------------------------------------------

class InstanceBadge(Badge):

    polymorphic_identity = 'instance'

    def assign(self, instance, creator):
        InstanceBadges.create(instance, self, creator)
        meta.Session.refresh(instance)
        meta.Session.refresh(self)


class InstanceBadges(Badges):

    def __init__(self, instance, badge, creator):
        self.instance = instance
        self.badge = badge
        self.creator = creator

    def __repr__(self):
        title = self.badge.title.encode('ascii', 'replace')
        return "<instancebadges(%s, badge %s/%s for instance%s)>" % (
            self.id, self.badge.id, title, self.instance.id)

    @classmethod
    def create(cls, instance, badge, creator):
        instancebadge = cls(instance, badge, creator)
        meta.Session.add(instancebadge)
        meta.Session.flush()
        return instancebadge


# --[ Delegateable Badges ]-------------------------------------------------

class DelegateableBadge(Badge):

    polymorphic_identity = 'delegateable'

    def assign(self, delegateable, creator):
        DelegateableBadges.create(delegateable, self, creator)
        meta.Session.refresh(delegateable)
        meta.Session.refresh(self)


class DelegateableBadges(Badges):

    def __init__(self, delegateable, badge, creator):
        self.delegateable = delegateable
        self.badge = badge
        self.creator = creator

    def __repr__(self):
        title = self.badge.title.encode('ascii', 'replace')
        return "<delegateablebadges(%s, badge %s/%s for delegateable%s)>" % (
            self.id, self.badge.id, title, self.delegateable.id)

    @classmethod
    def create(cls, delegateable, badge, creator):
        delegateablebadge = cls(delegateable, badge, creator)
        meta.Session.add(delegateablebadge)
        meta.Session.flush()
        return delegateablebadge


# --[ Category Badges ]-----------------------------------------------------


class CategoryBadge(DelegateableBadge):

    polymorphic_identity = 'category'

    @classmethod
    def create(cls, title, color, visible, description, instance=None,
               parent=None, select_child_description=u'', ):
        badge = cls(title, color, visible, description, instance)
        badge.parent = parent
        badge.select_child_description = select_child_description
        meta.Session.add(badge)
        meta.Session.flush()
        return badge

    def to_dict(self):
        d = super(CategoryBadge, self).to_dict()
        d['parent'] = self.parent
        d['select_child_description'] = self.select_child_description
        return d

    def is_ancester(self, badge):
        """
        returns True if the given badge is an ancester of self
        """
        if self == badge:
            return True
        elif self.parent is None:
            return False
        else:
            return self.parent.is_ancester(badge)

    def get_key(self, root=None, separator=u' > '):
        if self.parent is root:
            return self.title
        else:
            return u'%s%s%s' % (
                self.parent.get_key(root, separator),
                separator,
                self.title)
