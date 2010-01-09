from sqlalchemy import Column, Integer, Unicode

import meta
from meta import Base

class Group(Base):
    __tablename__ = 'group'
    
    CODE_ANONYMOUS = u"anonymous"
    CODE_OBSERVER = u"observer"
    CODE_VOTER = u"voter"
    CODE_SUPERVISOR = u"supervisor"
    CODE_ADMIN = u"admin"
    CODE_DEFAULT = u"default"    
    
    INSTANCE_GROUPS = [CODE_OBSERVER, CODE_VOTER, CODE_SUPERVISOR]
    INSTANCE_DEFAULT = CODE_VOTER
    
    id = Column(Integer, primary_key=True)
    group_name = Column(Unicode(255), nullable=False, unique=True)
    code = Column(Unicode(255), nullable=False, unique=True)
    description = Column(Unicode(1000))
        
    def __init__(self, group_name, code, description=None):
        self.group_name = group_name
        self.code = code
        self.description = description
        
    def __repr__(self):
        return u"<Group(%d,%s)>" % (self.id, self.code)
    
    @classmethod
    def all(cls):
        return meta.Session.query(Group).all()
    
    @classmethod
    def find(cls, group_name, instance_filter=True, include_deleted=False):
        try:
            return meta.Session.query(Group).filter(Group.group_name==group_name).one()
        except: 
            return None
        
    def _index_id(self):
        return self.group_name
    
    
    @classmethod
    def by_id(cls, id):
        try:
            return meta.Session.query(Group).filter(Group.id==id).one()
        except: 
            return None
        
    @classmethod
    def by_code(cls, code):
        try:
            return meta.Session.query(Group).filter(Group.code==code).one()
        except: 
            return None
        
