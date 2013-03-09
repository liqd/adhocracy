import logging

from sqlalchemy import Table, Column, ForeignKey, Integer, Unicode

import meta

log = logging.getLogger(__name__)

group_permission_table = Table(
    'group_permission', meta.data,
    Column('group_id', Integer, ForeignKey('group.id',
           onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permission.id',
           onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)

permission_table = Table(
    'permission', meta.data,
    Column('id', Integer, primary_key=True),
    Column('permission_name', Unicode(255), nullable=False, unique=True)
)


class Permission(object):

    def __init__(self, permission_name):
        self.permission_name = unicode(permission_name)

    @classmethod
    def find(cls, permission_name, instance_filter=True,
             include_deleted=False):
        try:
            q = meta.Session.query(Permission)
            q = q.filter(Permission.permission_name ==
                         unicode(permission_name))
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (permission_name, e))
            return None

    @classmethod
    def find_multiple(cls, permission_names):
        return meta.Session.query(Permission).filter(
            Permission.permission_name.in_(permission_names)).all()

    _index_id = 'permission_name'

    @classmethod
    def all(cls):
        return meta.Session.query(Permission).all()

    def __repr__(self):
        return u"<Permission(%d,%s)>" % (self.id, self.permission_name)
