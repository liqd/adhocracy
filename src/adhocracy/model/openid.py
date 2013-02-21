from datetime import datetime

import logging

from sqlalchemy import Table, Column, ForeignKey, or_
from sqlalchemy import DateTime, Integer, LargeBinary, Unicode
import meta

log = logging.getLogger(__name__)


openid_table = Table(
    'openid', meta.data,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('identifier', Unicode(255), nullable=False, index=True)
)


oid_nonces = Table(
    'oid_nonces', meta.data,
    Column('server_url', LargeBinary, nullable=False),
    Column('timestamp', Integer, primary_key=True),
    Column('salt', Unicode(40), nullable=False, index=True)
)


oid_associations = Table(
    'oid_associations', meta.data,
    Column('server_url', LargeBinary, nullable=False),
    Column('handle', Unicode(255), nullable=False, index=True),
    Column('secret', LargeBinary, nullable=False),
    Column('issued', Integer, primary_key=True),
    Column('lifetime', Integer, primary_key=True),
    Column('assoc_type', Unicode(64), nullable=False)
)


class OpenID(object):

    def __init__(self, identifier, user):
        self.identifier = identifier
        self.user = user

    @classmethod
    def find(cls, identifier, include_deleted=False):
        try:
            q = meta.Session.query(OpenID)
            q = q.filter(OpenID.identifier == identifier)
            if not include_deleted:
                q = q.filter(or_(OpenID.delete_time == None,
                                 OpenID.delete_time > datetime.utcnow()))
            return q.one()
        except Exception, e:
            log.warn("find(%s): %s" % (identifier, e))
            return None

    @classmethod
    def by_id(cls, id, include_deleted=False):
        try:
            q = meta.Session.query(OpenID)
            q = q.filter(OpenID.id == id)
            if not include_deleted:
                q = q.filter(or_(OpenID.delete_time == None,
                                 OpenID.delete_time > datetime.utcnow()))
            return q.limit(1).first()
        except Exception:
            log.exception("by_id(%s)" % id)
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
        return u"<OpenID(%d,%s,%s)>" % (self.id,
                                        self.identifier,
                                        self.user.user_name)
