import hashlib
import os
import logging
from datetime import datetime

from sqlalchemy import Column, Integer, Unicode, UnicodeText, Boolean, DateTime, func, or_
from sqlalchemy.orm import synonym
from sqlalchemy.ext.associationproxy import association_proxy

from babel import Locale

import meta
import filter as ifilter
from meta import Base
import group

log = logging.getLogger(__name__)

class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True)
    user_name = Column(Unicode(255), nullable=False, unique=True, index=True)
    display_name = Column(Unicode(255), nullable=True, index=True)
    bio = Column(UnicodeText(), nullable=True)
    email = Column(Unicode(255), nullable=True, unique=False)
    email_priority = Column(Integer, default=4)
    activation_code = Column(Unicode(255), nullable=True, unique=False)
    reset_code = Column(Unicode(255), nullable=True, unique=False)
    _password = Column('password', Unicode(80), nullable=False)
    _locale = Column('locale', Unicode(7), nullable=True)
    create_time = Column(DateTime, default=datetime.utcnow)
    access_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    delete_time = Column(DateTime)
    
    def __init__(self, user_name, email, password, display_name=None, bio=None):
        self.user_name = user_name
        self.email = email
        self.password = password
        self.display_name = display_name
        self.bio = bio
        
    def __repr__(self):
        return u"<User(%s,%s)>" % (self.id, self.user_name)
           
    def _get_name(self):
        return self.display_name.strip() \
            if self.display_name and len(self.display_name.strip()) > 0 \
            else self.user_name
    
    name = property(_get_name)
    
    def _get_locale(self):
        if not self._locale:
            return None
        return Locale.parse(self._locale)
    
    def _set_locale(self, locale):
        self._locale = str(locale)
        
    locale = synonym('_locale', descriptor=property(_get_locale,
                                                    _set_locale))
    
    def _get_alternatives(self):
        return []
    
    def _set_alternatives(self, alternatives):
        pass
    
    alternatives = property(_get_alternatives, _set_alternatives)
    
    def _get_context_groups(self):
        groups = []
        for membership in self.memberships: 
            if membership.is_expired():
                continue
            if not membership.instance or \
                membership.instance == ifilter.get_instance():
                groups.append(membership.group)
        return groups
     
    groups = property(_get_context_groups)
    
    def _has_permission(self, permission_name):
        for group in self.groups:
            for perm in group.permissions:
                if perm.permission_name == permission_name:
                    return True
        return False
    
    def is_member(self, instance):
        for membership in self.memberships:
            if (not membership.is_expired()) and \
                membership.instance == instance:
                return True
        return False
    
    def _get_instances(self):
        instances = []
        for membership in self.memberships:
            if (not membership.is_expired()) and \
                (membership.instance is not None):
                instances.append(membership.instance)
        return list(set(instances))
    
    instances = property(_get_instances)
    
    def _get_twitter(self):
        for twitter in self.twitters:
            if not twitter.delete_time:
                return twitter
        return None
    
    twitter = property(_get_twitter)
    
    def _set_password(self, password):
        """Hash password on the fly."""
        
        if isinstance(password, unicode):
            password_8bit = password.encode('UTF-8')
        else:
            password_8bit = password
        
        salt = hashlib.sha1(os.urandom(60))
        hash = hashlib.sha1(password_8bit + salt.hexdigest())
        hashed_password = salt.hexdigest() + hash.hexdigest()
        
        if not isinstance(hashed_password, unicode):
            hashed_password = hashed_password.decode('UTF-8')
        
        self._password = hashed_password
    
    def _get_password(self):
        """Return the password hashed"""
        return self._password
    
    password = synonym('_password', descriptor=property(_get_password,
                                                        _set_password))
    
    def validate_password(self, password):
        """
        Check the password against existing credentials.
        
        :param password: the password that was provided by the user to
            try and authenticate. This is the clear text version that we will
            need to match against the hashed one in the database.
        :type password: unicode object.
        :return: Whether the password is valid.
        :rtype: bool
        """
        hashed_pass = hashlib.sha1(password + self.password[:40])
        return self.password[40:] == hashed_pass.hexdigest()
    
    @classmethod
    def complete(cls, prefix, limit=5, instance_filter=True):
        q = meta.Session.query(User)
        prefix = prefix.lower()
        q = q.filter(or_(func.lower(User.user_name).like(prefix + "%"),
                         func.lower(User.display_name).like(prefix + "%")))
        q = q.limit(limit)
        completions = q.all()
        if ifilter.has_instance() and instance_filter:
            inst = ifilter.get_instance()
            completions = filter(lambda u: u.is_member(inst), completions)
        return completions 
    
    @classmethod
    def find(cls, user_name, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(User)
            q = q.filter(User.user_name==unicode(user_name))
            if not include_deleted:
                q = q.filter(or_(User.delete_time==None,
                                 User.delete_time>datetime.utcnow()))
            user = q.one()
            if ifilter.has_instance() and instance_filter:
                user = user.is_member(ifilter.get_instance()) and user or None
            return user
        except Exception: 
            log.exception("find(%s)" % id)
            return None
    
    def _index_id(self):
        return self.user_name
    
    @classmethod
    def all(cls, instance_filter=True, include_deleted=False):
        q = meta.Session.query(User)
        if not include_deleted:
            q = q.filter(or_(User.delete_time==None,
                             User.delete_time>datetime.utcnow()))
        users = q.all()
        if ifilter.has_instance() and instance_filter:
            users = filter(lambda user: user.is_member(ifilter.get_instance()), 
                           users)
        return users
    
    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
               self.delete_time<=at_time
    
    def delegation_node(self, scope):
        from adhocracy.lib.democracy import DelegationNode
        return DelegationNode(self, scope)
    
    def number_of_votes_in_scope(self, scope):
        """
        May be a bit too much as multiple delegations are counted for each user
        they are delegated to. (This is the safety net delegation)
        """
        return self.delegation_node(scope).number_of_delegations() + 1
    
    def delegate_to_user_in_scope(self, target_user, scope):
        from adhocracy.lib.democracy import DelegationNode
        return DelegationNode.create_delegation(from_user=self, to_user=target_user, scope=scope)
    
    # REFACT: rename: orientation doesn't really ring a bell. decision seems better but isn't
    def vote_for_proposal(self, proposal, orientation):
        # REFACT: proposals don't automatically have a poll - this is dangeorus
        from adhocracy.lib.democracy.decision import Decision
        return Decision(self, proposal.poll).make(orientation)
    

