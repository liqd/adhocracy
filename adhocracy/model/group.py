import logging

from sqlalchemy import Table, Column, Integer, Unicode

import meta

log = logging.getLogger(__name__)

group_table = Table('group', meta.data, 
    Column('id', Integer, primary_key=True),
    Column('group_name', Unicode(255), nullable=False, unique=True),
    Column('code', Unicode(255), nullable=False, unique=True),
    Column('description', Unicode(1000))
    )


class Group(object):
    
    CODE_ANONYMOUS = u"anonymous"
    CODE_OBSERVER = u"observer"
    CODE_VOTER = u"voter"
    CODE_SUPERVISOR = u"supervisor"
    CODE_ADMIN = u"admin"
    CODE_DEFAULT = u"default"    
    
    INSTANCE_GROUPS = [CODE_OBSERVER, CODE_VOTER, CODE_SUPERVISOR]
    INSTANCE_DEFAULT = CODE_VOTER
        
    def __init__(self, group_name, code, description=None):
        self.group_name = group_name
        self.code = code
        self.description = description
    
        
    @classmethod
    def all(cls):
        return meta.Session.query(Group).all()
        
        
    @classmethod
    def all_instance(cls):
        # todo: one query. 
        return [cls.by_code(g) for g in cls.INSTANCE_GROUPS] 
    
    
    @classmethod
    def find(cls, group_name, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Group)
            q = q.filter(Group.group_name==group_name)
            return q.limit(1).first()
        except Exception, e: 
            log.warn("find(%s): %s" % (id, e))
            return None
    
        
    def _index_id(self):
        return self.group_name
    
    
    @classmethod
    def by_id(cls, id):
        q = meta.Session.query(Group)
        q = q.filter(Group.id==id)
        return q.limit(1).first()
    
        
    @classmethod
    def by_code(cls, code):
        q = meta.Session.query(Group)
        q = q.filter(Group.code==code)
        return q.limit(1).first()
    
    
    def __repr__(self):
        return u"<Group(%d,%s)>" % (self.id, self.code)
    
        
