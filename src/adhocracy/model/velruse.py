from datetime import datetime

import logging

from sqlalchemy import Table, Column, ForeignKey, or_, UniqueConstraint
from sqlalchemy import DateTime, Integer, Unicode

import meta

log = logging.getLogger(__name__)


velruse_table = Table(
    'velruse', meta.data,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('domain', Unicode(255), nullable=False, index=True),
    Column('domain_user', Unicode(255), nullable=False, index=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    UniqueConstraint('domain', 'domain_user', name='unique_velruse_user'),
)


def filter_deleted(q):
    return q.filter(or_(Velruse.delete_time == None,  # noqa
                    Velruse.delete_time > datetime.utcnow()))


class Velruse(object):

    def __init__(self, domain, domain_user, adhocracy_user):
        self.domain = domain
        self.domain_user = domain_user
        self.user = adhocracy_user

    @classmethod
    def find(cls, domain, domain_user, include_deleted=False):
        try:
            q = meta.Session.query(Velruse)
            q = q.filter(Velruse.domain == domain,
                         Velruse.domain_user == domain_user)
            if not include_deleted:
                q = filter_deleted(q)
            return q.one()
        except Exception as e:
            log.warn("find(%s, %s): %s" % (domain, domain_user, e))
            return None

    @classmethod
    def find_any(cls, accounts, include_deleted=False):
        for account in accounts:
            velruse_account = Velruse.find(account['domain'],
                                           account['userid'],
                                           include_deleted)
            if velruse_account is not None:
                return velruse_account

        return None

    @classmethod
    def by_id(cls, id, include_deleted=False):
        try:
            q = meta.Session.query(Velruse)
            q = q.filter(Velruse.id == id)
            if not include_deleted:
                q = filter_deleted(q)
            return q.limit(1).first()
        except Exception as e:
            log.exception("by_id(%s): %s" % (id, e))
            return None

    @classmethod
    def by_user_and_domain(cls, user, domain, include_deleted=False):
        try:
            q = meta.Session.query(Velruse)
            q = q.filter(Velruse.user_id == user.id,
                         Velruse.domain == domain)
            if not include_deleted:
                q = filter_deleted(q)
            return q.all()
        except Exception as e:
            log.exception("by_user_and_domain(%s, %s): %s" % (user, domain, e))
            return None

    @classmethod
    def by_user_and_domain_first(cls, user, domain, include_deleted=False):
        try:
            q = meta.Session.query(Velruse)
            q = q.filter(Velruse.user_id == user.id,
                         Velruse.domain == domain)
            if not include_deleted:
                q = filter_deleted(q)
            return q.limit(1).first()
        except Exception as e:
            log.exception("by_user_and_domain_first(%s, %s): %s"
                          % (user, domain, e))
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

    def delete_forever(self):
        try:
            meta.Session.delete(self)
        except Exception as e:
            log.exception("delete_forever: %s" % e)
            return None

    @classmethod
    def connect(cls, adhocracy_user, domain, domain_user,
                velruse_email, email_verified=False):
        """
        Connect existing adhocracy user to velruse.
        """

        v = Velruse(unicode(domain), unicode(domain_user), adhocracy_user)

        if email_verified and velruse_email == adhocracy_user.email:
            adhocracy_user.set_email_verified()

        meta.Session.add(v)

        return v

    def __repr__(self):
        return u"<Velruse(%d,%s,%s,%s)>" % (self.id,
                                            self.domain,
                                            self.domain_user,
                                            self.user.user_name)
