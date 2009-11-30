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
    ``Motion``) and a ``User``. 
    
    **TODO:** Developing a good caching strategy for this class would be 
    useful in order to cache the delegation graph to memcached.
    
    :param user: The ``User`` at the center of this ``DelegationNode``.
    :param delegateable: A ``Delegateable``.   
    """
    
    def __init__(self, user, delegateable):
        self.user = user
        self.delegateable = delegateable
        
    def _query_traverse(self, querymod, recurse, at_time):
        #return []
        
        if not at_time:
            at_time = datetime.now()
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
    
    def inbound(self, recurse=True, at_time=None, filter=True):
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
        
        if filter:
            by_principal = dict()
            for delegation in set(delegations):
                by_principal[delegation.principal] = by_principal.get(delegation.principal, []) + [delegation]
            delegations = [self.filter_delegations(ds)[0] for ds in by_principal.values()]
        
        return delegations
    
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
            return []
        _path.append(self.user)
        
        delegations = self.inbound(recurse=recurse, at_time=at_time, filter=False)
        for delegation in list(delegations):
            ddnode = DelegationNode(delegation.principal, self.delegateable)
            delegations += ddnode.transitive_inbound(recurse=recurse, at_time=at_time,
                                                     _path=_path)
        return delegations
    
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
        
        now = datetime.now()  
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
        matches = [d for d in delegations]
        for d in delegations:
            for m in matches:
                if m.scope.is_super(d.scope):
                    matches.remove(m)
        return matches

