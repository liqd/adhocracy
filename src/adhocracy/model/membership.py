from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey, or_
from sqlalchemy import Integer, DateTime, Boolean

import instance_filter as ifilter
import meta

log = logging.getLogger(__name__)


membership_table = Table(
    'membership', meta.data,
    Column('id', Integer, primary_key=True),
    Column('approved', Boolean, nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('expire_time', DateTime, nullable=True),
    Column('access_time', DateTime, default=datetime.utcnow,
           onupdate=datetime.utcnow),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=True),
    Column('group_id', Integer, ForeignKey('group.id'), nullable=False),
)


class Membership(object):

    def __init__(self, user, instance, group, approved=True):
        self.user = user
        self.instance = instance
        self.group = group
        self.approved = approved

    @classmethod
    def all_q(cls, instance_filter=True, include_deleted=False):
        q = meta.Session.query(Membership)
        if ifilter.has_instance() and instance_filter:
            q = q.filter(Membership.instance_id == ifilter.get_instance().id)
        if not include_deleted:
            q = q.filter(or_(Membership.expire_time == None,
                             Membership.expire_time > datetime.utcnow()))
        return q

    @classmethod
    def all(cls, instance_filter=True, include_deleted=False):
        return cls.all_q(instance_filter=instance_filter,
                         include_deleted=include_deleted).all()

    def expire(self, expire_time=None):
        if expire_time is None:
            expire_time = datetime.utcnow()
        if not self.is_expired(at_time=expire_time):
            self.expire_time = expire_time
        #if not self.user.is_member(self.instance):
        #    self.user.revoke_delegations(self.instance)

    def is_expired(self, at_time=None):
        if self.expire_time is None:
            return False
        else:
            if at_time is None:
                at_time = datetime.utcnow()
            return self.expire_time <= at_time

    def delete(self, delete_time=None):
        return self.expire(expire_time=delete_time)

    def is_deleted(self, at_time=None):
        return self.is_expired(at_time=at_time)

    def __repr__(self):
        key = self.instance and self.instance.key or "",
        return u"<Membership(%d,%s,%s,%s)>" % (self.id,
                                               self.user.user_name,
                                               key,
                                               self.group.code)
