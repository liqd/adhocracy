import logging

from sqlalchemy import Table, Column, Integer, Unicode, String, ForeignKey, DateTime, func, Boolean
from sqlalchemy.orm import relation, synonym, backref
from pylons import g

import meta
from meta import Base

log = logging.getLogger(__name__)

group_permission = Table('group_permission', Base.metadata,
    Column('group_id', Integer, ForeignKey('group.id',
        onupdate="CASCADE", ondelete="CASCADE")),
    Column('permission_id', Integer, ForeignKey('permission.id',
        onupdate="CASCADE", ondelete="CASCADE"))
)

class Permission(Base):
    __tablename__ = 'permission'
    
    id = Column(Integer, primary_key=True)
    permission_name = Column(Unicode(255), nullable=False, unique=True)
    
    groups = relation('Group', secondary=group_permission, lazy=False,
                          backref=backref('permissions', lazy=False))
    
    def __init__(self, permission_name):
        self.permission_name = permission_name
        
    def __repr__(self):
        return u"<Permission(%d,%s)>" % (self.id, self.code)
        
    @classmethod
    def find(cls, permission_name, instance_filter=True, include_deleted=False):
        try:
            return meta.Session.query(Permission).filter(Permission.permission_name==permission_name).one()
        except Exception, e: 
            log.warn("find(%s): %s" % (id, e))
            return None
        
    def _index_id(self):
        return self.permission_name
    
    @classmethod
    def all(cls):
        return meta.Session.query(Permission).all()