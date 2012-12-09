from datetime import datetime, timedelta
import logging
import math
import re

from babel import Locale

from sqlalchemy import Table, Column, ForeignKey, func, or_
from sqlalchemy import DateTime, Integer, Float, Boolean, Unicode, UnicodeText
from sqlalchemy.orm import reconstructor

import meta


log = logging.getLogger(__name__)


instance_table = \
    Table('instance', meta.data,
          Column('id', Integer, primary_key=True),
          Column('key', Unicode(20), nullable=False, unique=True),
          Column('label', Unicode(255), nullable=False),
          Column('description', UnicodeText(), nullable=True),
          Column('required_majority', Float, nullable=False),
          Column('activation_delay', Integer, nullable=False),
          Column('create_time', DateTime, default=func.now()),
          Column('access_time', DateTime, default=func.now(),
                 onupdate=func.now()),
          Column('delete_time', DateTime, nullable=True),
          Column('creator_id', Integer, ForeignKey('user.id'),
                 nullable=False),
          Column('default_group_id', Integer, ForeignKey('group.id'),
                 nullable=True),
          Column('allow_adopt', Boolean, default=True),
          Column('allow_delegate', Boolean, default=True),
          Column('allow_propose', Boolean, default=True),
          Column('allow_index', Boolean, default=True),
          Column('hidden', Boolean, default=False),
          Column('locale', Unicode(7), nullable=True),
          Column('css', UnicodeText(), nullable=True),
          Column('frozen', Boolean, default=False),
          Column('milestones', Boolean, default=False),
          Column('use_norms', Boolean, nullable=True, default=True),
          Column('require_selection', Boolean, nullable=True, default=False),
          Column('is_authenticated', Boolean, nullable=True, default=False),
          Column('hide_global_categories', Boolean, nullable=True, default=False),
          Column('editable_comments_default', Boolean, nullable=True, default=True)
          )


# Instance is not a delegateable - but it should - or you cannot do
# instance wide delegation


class Instance(meta.Indexable):
    __tablename__ = 'instance'

    INSTANCE_KEY = re.compile("^[a-zA-Z][a-zA-Z0-9-]{2,18}$")

    def __init__(self, key, label, creator, description=None):
        self.key = key
        self.label = label
        self.creator = creator
        self.description = description
        self.required_majority = 0.66
        self.activation_delay = 7
        self.allow_adopt = True
        self.allow_delegate = True
        self.allow_propose = True
        self.allow_index = True
        self.hidden = False
        self.frozen = False
        self.require_selection = False
        self._required_participation = None

    @reconstructor
    def _reconstruct(self):
        self._required_participation = None

    def _get_locale(self):
        if not self._locale:
            return None
        return Locale.parse(self._locale)

    def _set_locale(self, locale):
        self._locale = unicode(locale)

    locale = property(_get_locale, _set_locale)

    def current_memberships(self):
        return [m for m in self.memberships if not m.is_expired()]

    def members(self):
        '''
        return all users that are members of this instance through
        global or local membership
        '''
        from adhocracy.model.permission import Permission
        members = [membership.user for membership in
                   self.current_memberships()]
        global_membership = Permission.find('global.member')
        for group in global_membership.groups:
            for membership in group.memberships:
                if membership.instance == None and not membership.expire_time:
                    members.append(membership.user)
        return list(set(members))

    def _get_required_participation(self):
        if self._required_participation is None:
            from adhocracy.lib.democracy import Decision
            avg = Decision.average_decisions(self)
            required = int(math.ceil(max(2, avg * self.required_majority)))
            self._required_participation = required
        return self._required_participation

    required_participation = property(_get_required_participation)

    def _get_activation_timedelta(self):
        return timedelta(days=self.activation_delay)
        #return timedelta(minutes=self.activation_delay)

    activation_timedelta = property(_get_activation_timedelta)

    def _get_num_proposals(self):
        from proposal import Proposal
        q = meta.Session.query(Proposal)
        q = q.filter(Proposal.instance == self)
        q = q.filter(or_(Proposal.delete_time == None,
                         Proposal.delete_time >= datetime.utcnow()))
        return q.count()

    num_proposals = property(_get_num_proposals)

    def _get_num_members(self):
        from membership import Membership
        q = meta.Session.query(Membership)
        q = q.filter(Membership.instance == self)
        q = q.filter(or_(Membership.expire_time == None,
                         Membership.expire_time >= datetime.utcnow()))
        return q.count()

    num_members = property(_get_num_members)

    @classmethod
    #@meta.session_cached
    def find(cls, key, instance_filter=True, include_deleted=False):
        key = unicode(key).lower()
        try:
            q = meta.Session.query(Instance)
            try:
                q = q.filter(Instance.id == int(key))
            except ValueError:
                q = q.filter(Instance.key == unicode(key))
            if not include_deleted:
                q = q.filter(or_(Instance.delete_time == None,
                                 Instance.delete_time > datetime.utcnow()))
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (key, e))
            return None

    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
            self.delete_time <= at_time

    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        for delegateable in self.delegateables:
            delegateable.delete(delete_time)
        for membership in self.memberships:
            membership.expire(delete_time)
        if not self.is_deleted(delete_time):
            self.delete_time = delete_time

    def is_shown(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return not (self.is_deleted(at_time) or self.hidden)

    _index_id_attr = 'key'

    @classmethod
    def all_q(cls):
        return meta.Session.query(Instance)

    @classmethod
    def all(cls, limit=None, include_deleted=False, include_hidden=False):
        q = cls.all_q()
        q = meta.Session.query(Instance)
        if not include_deleted:
            q = q.filter(or_(Instance.delete_time == None,
                             Instance.delete_time > datetime.utcnow()))
        if not include_hidden:
            q = q.filter(or_(Instance.hidden == None,
                             Instance.hidden == False))
        if limit is not None:
            q = q.limit(limit)
        return q.all()

    @classmethod
    def create(cls, key, label, user, description=None, locale=None):
        from group import Group
        from membership import Membership
        from page import Page

        instance = Instance(unicode(key).lower(), label, user)
        instance.description = description
        instance.default_group = Group.by_code(Group.INSTANCE_DEFAULT)
        if locale is not None:
            instance.locale = locale
        meta.Session.add(instance)
        supervisor_group = Group.by_code(Group.CODE_SUPERVISOR)
        membership = Membership(user, instance, supervisor_group,
                                approved=True)
        meta.Session.add(membership)
        Page.create(instance, label, u"", user)
        meta.Session.flush()
        return instance

    def to_dict(self):
        from adhocracy.lib import helpers as h
        d = dict(id=self.id,
                 key=self.key,
                 label=self.label,
                 creator=self.creator.user_name,
                 required_majority=self.required_majority,
                 activation_delay=self.activation_delay,
                 allow_adopt=self.allow_adopt,
                 allow_delegate=self.allow_delegate,
                 allow_propose=self.allow_propose,
                 allow_index=self.allow_index,
                 hidden=self.hidden,
                 url=h.entity_url(self),
                 instance_url=h.instance.url(self),
                 default_group=self.default_group.code,
                 create_time=self.create_time)
        if self.description:
            d['description'] = self.description
        return d

    def to_index(self):
        from adhocracy.lib.event import stats as estats
        index = super(Instance, self).to_index()
        if self.hidden:
            index['skip'] = True
        index.update(dict(
            instance=self.key,
            title=self.label,
            tags=[],
            body=self.description,
            user=self.creator.user_name,
            activity=estats.instance_activity(self)
        ))
        return index

    def __repr__(self):
        return u"<Instance(%d,%s)>" % (self.id, self.key)
