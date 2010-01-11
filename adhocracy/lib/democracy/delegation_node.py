from datetime import datetime
import logging

from sqlalchemy import or_

import adhocracy.model as model
from adhocracy.model import Delegation

log = logging.getLogger(__name__)

class DelegationNode(object):
    """
    A ``DelegationNode`` describes a part of the voting delegation graph
    sorrounding a ``Delegateable`` (i.e. a ``Category``, ``Issue`` or 
    ``Proposal``) and a ``User``. 
    
    **TODO:** Developing a good caching strategy for this class would be 
    useful in order to cache the delegation graph to memcached.
    
    :param user: The ``User`` at the center of this ``DelegationNode``.
    :param delegateable: A ``Delegateable``.   
    """
    
    def __init__(self, user, delegateable):
        self.user = user
        self.delegateable = delegateable
    
    def _query_traverse(self, querymod, recurse, at_time=None):
        if not at_time: # shouldn't this be if at_time is None: ?
            at_time = datetime.utcnow()
        
        query = model.meta.Session.query(Delegation)
        query = query.filter(Delegation.scope==self.delegateable)
        query = query.filter(Delegation.create_time<=at_time)
        query = query.filter(or_(Delegation.revoke_time == None,
                                 Delegation.revoke_time > at_time))
        query = querymod(query)
        delegations = query.all()
        if recurse:
            for parent in self.delegateable.parents:
                node = DelegationNode(self.user, parent)
                delegations += node._query_traverse(querymod, recurse, at_time)
        return delegations
    
    def inbound(self, recurse=True, at_time=None, should_filter=True):
        """
        Retrieve all inbound delegations (i.e. those that the user has received
        from other users in order to vote on their behalf) that apply to the 
        ``Delegateable``. 
        
        :param recurse: if ``True``, search will include delegations on parent 
            ``Delegateables`` in breadth-first traversal order.
        :param at_time: return the delegation graph at the given time, defaults
            to the current time. 
        :returns: list of ``Delegation``
        """
        delegations = self._query_traverse(lambda q: q.filter(Delegation.agent==self.user),
                                           recurse, at_time)
        if should_filter:
            by_principal = dict()
            for delegation in set(delegations):
                by_principal[delegation.principal] = by_principal.get(delegation.principal, []) + [delegation]
            delegations = [self.filter_delegations(ds)[0] for ds in by_principal.values()]
        
        delegations = self._filter_out_overridden_delegations(delegations)
        return self._filter_out_overrides_by_direct_vote(delegations)
    
    def transitive_inbound(self, recurse=True, at_time=None, _path=None):
        """
        Retrieve inbound delegations recursing through the delegation graph as well 
        as through the category tree.
        
        :param recurse: if ``True``, search will include delegations on parent 
            ``Delegateables`` in breadth-first traversal order.
        :param at_time: return the delegation graph at the given time, defaults
            to the current time. 
        :returns: list of ``Delegation``
        """
        if _path == None:
            _path = []
        elif self.user in _path: 
            return [] # we already visited this node
        # circle detection uses this path of visited nodes
        _path.append(self.user)
        
        delegations = self.inbound(recurse=recurse, at_time=at_time, should_filter=False)
        for delegation in list(delegations):
            ddnode = DelegationNode(delegation.principal, self.delegateable)
            additional_delegations = ddnode.transitive_inbound(recurse=recurse, at_time=at_time, _path=_path)
            for additional_delegation in additional_delegations:
                if additional_delegation.principal in _path:
                    continue # this is a delegation from  a node we already visited
                else:
                    delegations.append(additional_delegation)
        # This is used as a stack in the recursion - so we need to remove what we added in going into the recursion
        _path.remove(self.user)
        return delegations
    
    def number_of_votes(self):
        """Returns the number of votes this user has in this poll"""
        own_vote = 1
        return len(self.transitive_inbound()) + own_vote
    
    def outbound(self, recurse=True, at_time=None, filter=True):
        """
        Retrieve all outbound delegations (i.e. those that the user has given
        to other users in order allow them to vote on his/her behalf) that 
        apply to the ``Delegateable``. 
        
        :param recurse: if ``True``, search will include delegations on parent 
            ``Delegateables`` in breadth-first traversal order.
        :param at_time: return the delegation graph at the given time, defaults
            to the current time. 
        :returns: list of ``Delegation``
        """
        delegations = self._query_traverse(lambda q: q.filter(Delegation.principal==self.user),
                                           recurse, at_time)
        
        if filter:
            by_agent = dict()
            for delegation in set(delegations):
                by_agent[delegation.agent] = by_agent.get(delegation.agent, []) + [delegation]
            delegations = [self.filter_delegations(ds)[0] for ds in by_agent.values()]
        
        return delegations
    # TODO: consider to add a transitive-outbound to know where the vote will end up for a specific issue
    
    def propagate(self, callable, _edge=None, _propagation_path=None):
        """
        Propagate a given action along the delegation graph *against* its direction, 
        i.e. from the agent node towards its principal. This is the natural direction 
        to propagate actions along this network since it allows principals to reproduce
        the actions of their agents. 
        
        Propagation will abort on circular dependencies but has no recursion depth limit.
        
        :param callable: A callable that is to be called on each node. It must take 
            three arguments, a ``User``, a ``Delegateable`` and the ``Delegation`` 
            which served as a transitory edge during the last step of the propagation. 
        :returns: a list of all results produced by the callable. 
        """
        if not _propagation_path:
            _propagation_path = [self]
        elif self in _propagation_path:
            return []
        else: 
            _propagation_path.append(self)
        
        result = [callable(self.user, self.delegateable, _edge)] 
        for delegation in self.inbound():
            node = DelegationNode(delegation.principal, self.delegateable)
            result += node.propagate(callable, 
                                     _edge=delegation, 
                                     _propagation_path=_propagation_path)
        return result
    
    @classmethod
    def detach(cls, user, instance):
        """
        Detach a ``User`` from the delegation graph by destroying any 
        delegations the user might have issued. This operation in necessary 
        in cases when the user loses voting privileges. Since authorization 
        is not a part of the voting logic (it is handled on a higher level), 
        it is important to avoid delegated voting propagation towards the 
        user. Otherwise the user would still cast votes when pre-existing 
        delegations match.
        
        :param user: The user to be detached.
        :param instance: Instance for which to detach the graph. 
        """
        log.info("Purging delegation graph for %s in %s" % (repr(user), repr(instance)))
        
        now = datetime.utcnow()  
        query = model.meta.Session.query(Delegation)
        query = query.filter(Delegation.agent==user)
        query = query.filter(or_(Delegation.revoke_time == None,
                                 Delegation.revoke_time > now))
        for d in query.all():
            if d.scope.instance == instance:
                d.revoke_time = now
                model.meta.Session.add(d)
        model.meta.Session.commit()
    
    def __repr__(self):
        return "<DelegationNode(%s,%s)>" % (self.user.user_name, 
                                            self.delegateable.id)
    
    def __eq__(self, other):
        return self.user == other.user and \
               self.delegateable == other.delegateable
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    @classmethod
    def filter_delegations(cls, delegations):
        """
        Given a set of delegations, remove those that are overriden by others. 
        A delegation is overridden whenever there is another delegation with a
        narrower scope that still applies. 
        
        :param delegations: The list of delegations that are to be filtered. 
        :returns: A filtered list of delegations.
        """
        matches = list(delegations)
        for d in delegations:
            for m in matches:
                if m.scope.is_super(d.scope):
                    matches.remove(m)
        return matches
    
    @classmethod
    def create_delegation(cls, from_user, to_user, scope):
        delegation = model.Delegation(from_user, to_user, scope)
        # dwt: why do I need to add the delegation to the session here?
        # it should just be added via the relation it has to the user and 
        # either not be in the session at all or automatically via the user object
        model.meta.Session.add(delegation)
        # dwt: Why is the flush here neccessary? - supplies the id of course - but is that needed?
        model.meta.Session.flush()
        return delegation
    

    def _filter_out_overrides_by_direct_vote(self, delegations):
        from adhocracy.lib.democracy.decision import Decision
        def is_overriden_by_own_decision(delegation):
            if not hasattr(delegation.scope, 'poll'):
                return True # scope doesn't have polls -> can't self decide
            if delegation.scope.poll is None:
                return True # currently no poll in this cope -> can't self decide
            decision = Decision(delegation.principal, delegation.scope.poll)
            return not decision.is_self_decided()
            
        return filter(is_overriden_by_own_decision, delegations)
    
    def _filter_out_overridden_delegations(self, delegations):
        def is_overriden_by_other_delegation(delegation):
            node = DelegationNode(delegation.principal, self.delegateable)
            outbound_delegations = node.outbound()
            if 1 == len(outbound_delegations):
                return outbound_delegations[0].agent == self.user
            elif len(outbound_delegations) > 1:
                for delegation in outbound_delegations:
                    if delegation.agent == self.user and delegation.scope == self.delegateable:
                        return True
            return False
        return filter(is_overriden_by_other_delegation, delegations)
    
