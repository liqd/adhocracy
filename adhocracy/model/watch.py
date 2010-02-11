import logging
from datetime import datetime

from sqlalchemy import Table, Column, Integer, Unicode, ForeignKey, DateTime, func, or_

import meta

log = logging.getLogger(__name__)


watch_table = Table('watch', meta.data,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('entity_type', Unicode(255), nullable=False, index=True),
    Column('entity_ref', Unicode(255), nullable=False, index=True)                
    )


class Watch(object):
    
    def __init__(self, user, entity_type, entity_ref):
        self.user = user
        self.entity_type = entity_type
        self.entity_ref = entity_ref
    
    @classmethod
    def by_id(cls, id, include_deleted=False):
        try:
            q = meta.Session.query(Watch)
            q = q.filter(Watch.id==id)
            if not include_deleted:
                q = q.filter(or_(Watch.delete_time==None,
                                 Watch.delete_time>datetime.utcnow()))
            return q.one()
        except:
            return None
    
    @classmethod
    def find(cls, user, ref, include_deleted=False):
        try:
            q = meta.Session.query(Watch)
            q = q.filter(Watch.user==user)
            q = q.filter(Watch.entity_ref==ref)
            if not include_deleted:
                q = q.filter(or_(Watch.delete_time==None,
                                 Watch.delete_time>datetime.utcnow()))
            return q.one()
        except Exception, e:
            log.warn("find(%s:%s): %s" % (user, ref, e))
    
    @classmethod
    def all(cls, include_deleted=False):
        q = meta.Session.query(Watch)
        if not include_deleted:
            q = q.filter(or_(Watch.delete_time==None,
                             Watch.delete_time>datetime.utcnow()))
        return q.all()
        
    
    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        if not self.is_deleted(delete_time):
            self.delete_time = delete_time
            
    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
               self.delete_time<=at_time
    
    def __repr__(self):
        return "<Watch(%s,%s,%s)>" % (self.id, self.user.user_name, self.entity_ref)

        