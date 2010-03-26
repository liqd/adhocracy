import re
from datetime import datetime, timedelta
import logging

from sqlalchemy import Table, Column, Integer, Float, Boolean, Unicode, UnicodeText, ForeignKey, DateTime, func, or_
from sqlalchemy.orm import reconstructor

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
    Column('default_group_id', Integer, ForeignKey('group.id'), nullable=True),
    Column('allow_adopt', Boolean, default=True),       
    Column('allow_delegate', Boolean, default=True),
    Column('allow_index', Boolean, default=True),
    Column('hidden', Boolean, default=False)   
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
        self.allow_adopt = True
        self.allow_delegate = True
        self.allow_index = True
        self.hidden = False
        self._required_participation = None
    
    
    @reconstructor
    def _reconstruct(self):
        self._required_participation = None
        
    
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
    
    
    def _get_required_participation(self):
        if self._required_participation is None:
            from adhocracy.lib.democracy import Decision
            avg = Decision.average_decisions(self)
            self._required_participation = max(2, avg * self.required_majority)
        return self._required_participation
        
    required_participation = property(_get_required_participation)
    
    
    def _get_activation_timedelta(self):
        return timedelta(days=self.activation_delay)
        #return timedelta(minutes=self.activation_delay)
        
    activation_timedelta = property(_get_activation_timedelta)
    
    
    def _get_num_issues(self):
        from issue import Issue
        q = meta.Session.query(Issue)
        q = q.filter(Issue.instance==self)
        q = q.filter(or_(Issue.delete_time==None,
                         Issue.delete_time>=datetime.utcnow()))
        return q.count()
        
    num_issues = property(_get_num_issues)

    
    def _get_num_proposals(self):
        from proposal import Proposal
        q = meta.Session.query(Proposal)
        q = q.filter(Proposal.instance==self)
        q = q.filter(or_(Proposal.delete_time==None,
                         Proposal.delete_time>=datetime.utcnow()))
        return q.count()
        
    num_proposals = property(_get_num_proposals)
    
    
    def _get_num_members(self):
        from membership import Membership
        q = meta.Session.query(Membership)
        q = q.filter(Membership.instance==self)
        q = q.filter(or_(Membership.expire_time==None,
                         Membership.expire_time>=datetime.utcnow()))
        return q.count()
        
    num_members = property(_get_num_members)
    
    
    @classmethod
    def find(cls, key, instance_filter=True, include_deleted=False):
        key = unicode(key).lower()
        try:
            q = meta.Session.query(Instance)
            try:
                q = q.filter(Instance.id==int(key))
            except ValueError:
                q = q.filter(Instance.key==unicode(key))
            if not include_deleted:
                q = q.filter(or_(Instance.delete_time==None,
                                 Instance.delete_time>datetime.utcnow()))
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (key, e))
            return None
    
    
    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
               self.delete_time<=at_time
               
    
    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        for delegateable in self.delegateables:
            delegateable.delete(delete_time)
        for membership in self.memberships:
            membership.expire(delete_time)
    
    
    def _index_id(self):
        return self.key
    
    
    @classmethod  
    def all(cls, limit=None):
        q = meta.Session.query(Instance)
        if limit is not None:
            q = q.limit(limit)
        return q.all()
    
    
    @classmethod  
    def create(cls, key, label, user, description=None):
        import adhocracy.lib.text as libtext
        from group import Group
        from membership import Membership
         
        instance = Instance(unicode(key).lower(), label, user)
        if description is not None:
            instance.description = libtext.cleanup(description)
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
                 allow_adopt=self.allow_adopt,
                 default_group=self.default_group.code,
                 create_time=self.create_time)
        if self.description:
            d['description'] = self.description
        #d['members'] = map(lambda u: u.user_name, self.members)
        return d
    
    def __repr__(self):
        return u"<Instance(%d,%s)>" % (self.id, self.key)
    
