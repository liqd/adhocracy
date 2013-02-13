from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey, or_
from sqlalchemy import DateTime, Integer

import meta
import instance_filter as ifilter
from delegateable import Delegateable

log = logging.getLogger(__name__)


delegation_table = Table(
    'delegation', meta.data,
    Column('id', Integer, primary_key=True),
    Column('agent_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('principal_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('scope_id', Integer, ForeignKey('delegateable.id'), nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('revoke_time', DateTime, default=None, nullable=True)
)


class Delegation(object):

    def __init__(self, principal, agent, scope):
        self.principal = principal
        self.agent = agent
        self.scope = scope

    def is_match(self, delegateable, include_deleted=False):
        if include_deleted or not self.is_revoked():
            return (self.scope == delegateable or
                    self.scope.is_super(delegateable))
        return False

    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Delegation)
            q = q.filter(Delegation.id == id)
            if not include_deleted:
                q = q.filter(or_(Delegation.revoke_time == None,
                                 Delegation.revoke_time > datetime.utcnow()))
            d = q.one()
            if ifilter.has_instance() and instance_filter:
                if d.scope.instance != ifilter.get_instance():
                    return None
            return d
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None

    @classmethod
    def find_by_agent_principal_scope(cls, agent, principal, scope,
                                      instance_filter=True,
                                      include_deleted=False):
        try:
            q = meta.Session.query(Delegation)
            q = q.filter(Delegation.agent == agent)
            q = q.filter(Delegation.principal == principal)
            q = q.filter(Delegation.scope == scope)
            if not include_deleted:
                q = q.filter(or_(Delegation.revoke_time == None,
                                 Delegation.revoke_time > datetime.utcnow()))
            d = q.one()
            if ifilter.has_instance() and instance_filter:
                if d.scope.instance != ifilter.get_instance():
                    return None
            return d
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None

    @classmethod
    def find_by_principal(cls, principal, include_deleted=False):
        try:
            q = meta.Session.query(Delegation)
            q = q.filter(Delegation.principal == principal)
            if not include_deleted:
                q = q.filter(or_(Delegation.revoke_time == None,
                                 Delegation.revoke_time > datetime.utcnow()))
            return q.all()
        except Exception, e:
            log.warn("find_by_principal(%s): %s" % (id, e))
            return None

    @classmethod
    def find_by_principal_in_scope(cls, principal, scope,
                                   include_deleted=False):
        principals = cls.find_by_principal(principal,
                                           include_deleted=include_deleted)
        return [d for d in principals if
                d.is_match(scope, include_deleted=include_deleted)]

    @classmethod
    def all(cls, instance=None, include_deleted=False):
        q = meta.Session.query(Delegation)
        q = q.join(Delegateable)
        if not include_deleted:
            q = q.filter(or_(Delegation.revoke_time == None,
                             Delegation.revoke_time > datetime.utcnow()))
        if instance is not None:
            q = q.filter(Delegateable.instance == instance)
        return q.all()

    @classmethod
    def create(cls, principal, agent, scope, replay=True):
        from adhocracy.lib.democracy import Decision
        delegation = Delegation(principal, agent, scope)
        meta.Session.add(delegation)
        meta.Session.flush()
        if replay:
            log.debug("Replaying the vote for Delegation: %s" % delegation)
            Decision.replay_decisions(delegation)
        return delegation

    def revoke(self, revoke_time=None):
        if revoke_time is None:
            revoke_time = datetime.utcnow()
        if self.revoke_time is None:
            self.revoke_time = revoke_time

    def delete(self, delete_time=None):
        self.revoke(revoke_time=delete_time)

    def is_revoked(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return ((self.revoke_time is not None) and
                self.revoke_time <= at_time)

    is_deleted = is_revoked

    def to_dict(self):
        from adhocracy.lib import helpers as h
        return dict(id=self.id,
                    url=h.entity_url(self),
                    create_time=self.create_time,
                    principal=self.principal.user_name,
                    agent=self.agent.user_name,
                    scope=self.scope_id)

    def __repr__(self):
        return u"<Delegation(%s, %s->%s, %s)>" % (
            self.id,
            self.principal.user_name,
            self.agent.user_name,
            self.scope.id
        )
