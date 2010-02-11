import re
from datetime import datetime
import logging

from sqlalchemy import Table, Column, Integer, Float, Unicode, UnicodeText, ForeignKey, DateTime, func, or_

import meta

log = logging.getLogger(__name__)

instance_table = Table('instance', meta.data,
    Column('id', Integer, primary_key=True),
    Column('key', Unicode(20), nullable=False, unique=True),
    Column('label', Unicode(255), nullable=False),
    Column('description', UnicodeText(), nullable=True),
    Column('required_majority', Float, nullable=False),
    Column('activation_delay', Integer, nullable=False),
    Column('create_time', DateTime, default=func.now()),
    Column('access_time', DateTime, default=func.now(), onupdate=func.now()),
    Column('delete_time', DateTime, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('default_group_id', Integer, ForeignKey('group.id'), nullable=True)    
    )

# Instance is not a delegateable - but it should - or you cannot do instance wide delegation
class Instance(object):
    __tablename__ = 'instance'
    
    INSTANCE_KEY = re.compile("^[a-zA-Z][a-zA-Z0-9_]{2,18}$")
    
        
    def __init__(self, key, label, creator, description=None):
        self.key = key
        self.label = label
        self.creator = creator
        self.description = description
        self.required_majority = 0.66
        self.activation_delay = 7
    
    
    def current_memberships(self):
        return [m for m in self.memberships if not m.is_expired()]
    
    def _get_members(self):
        members = self.current_memberships()
        global_membership = model.Permission.by_code('global.member')
        for group in global_membership.groups:
            for membership in group.memberships:
                if membership.instance == None and not membership.expire_time:
                    members.append(membership.user)
        return members
    
    members = property(_get_members)
    
    @classmethod
    def find(cls, key, instance_filter=True, include_deleted=False):
        key = unicode(key.lower())
        try:
            q = meta.Session.query(Instance)
            try:
                q = q.filter(Instance.id==int(key))
            except ValueError:
                q = q.filter(Instance.key==unicode(key))
            if not include_deleted:
                q = q.filter(or_(Instance.delete_time==None,
                                 Instance.delete_time>datetime.utcnow()))
            return q.one()
        except Exception, e:
            log.warn("find(%s): %s" % (key, e))
            return None
    
    
    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
               self.delete_time<=at_time
    
    
    def _index_id(self):
        return self.key
    
    
    @classmethod  
    def all(cls):
        return meta.Session.query(Instance).all()
    
    
    @classmethod  
    def create(cls, key, label, user, description=None):
        import adhocracy.lib.text as libtext
        from group import Group
        from membership import Membership
         
        instance = Instance(key, label, user)
        if description is not None:
            instance.description = text.cleanup(description)
        instance.default_group = Group.by_code(Group.INSTANCE_DEFAULT)
        meta.Session.add(instance)
        supervisor_group = Group.by_code(Group.CODE_SUPERVISOR)
        membership = Membership(user, instance, supervisor_group, 
                                approved=True)
        meta.Session.add(membership)
        meta.Session.flush()
        return instance
    
    
    def to_dict(self):
        d = dict(id=self.id,
                 key=self.key,
                 label=self.label,
                 creator=self.creator.user_name,
                 required_majority=self.required_majority,
                 activation_delay=self.activation_delay,
                 default_group=self.default_group.code,
                 create_time=self.create_time)
        if self.description:
            d['description'] = self.description
        #d['members'] = map(lambda u: u.user_name, self.members)
        return d
    
    def __repr__(self):
        return u"<Instance(%d,%s)>" % (self.id, self.key)
    
