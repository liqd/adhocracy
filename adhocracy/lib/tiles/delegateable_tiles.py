from datetime import datetime

from util import BaseTile

from pylons import request, response, session, tmpl_context as c

from .. import democracy
from .. import helpers as h
from .. import authorization as auth
import adhocracy.model as model

class DelegateableTile(BaseTile):
    
    def __init__(self, delegateable):
        self.delegateable = delegateable
        self.__dnode = None
        self.__delegations = None
        self.__num_principals = None
    
    def _dnode(self):
        if not self.__dnode:
            self.__dnode = democracy.DelegationNode(c.user, self.delegateable)
        return self.__dnode
    
    dnode = property(_dnode)
    
    def _delegations(self):
        if not self.__delegations:
            self.__delegations = self.dnode.outbound()
        return self.__delegations
    
    delegations = property(_delegations)
    
    def _num_principals(self):
        if self.__num_principals == None:
            principals = set(map(lambda d: d.principal, 
                                 self.dnode.transitive_inbound()))
            self.__num_principals = len(principals)
        return self.__num_principals
    
    num_principals = property(_num_principals)
    
    def _has_delegated(self):
        return len(self.delegations) > 0
    
    has_delegated = property(_has_delegated)
    
    def _has_overridden(self):
        return False
    
    has_overridden = property(_has_overridden)      
    
    @classmethod
    def prop_has_permkarma(cls, perm, allow_creator=True):
        return lambda self: auth.on_delegateable(self.delegateable, perm,
                                                 allow_creator=allow_creator)
    
    can_vote = property(BaseTile.prop_has_perm('vote.cast'))
    can_delegate = can_vote

    def _latest_comment(self):
        def dgb_latest(dgb):
            query = model.meta.Session.query(model.Revision.create_time)
            query = query.join(model.Comment)
            query = query.filter(model.Comment.topic==dgb)
            query = query.order_by(model.Revision.create_time.desc())
            return query.one()[0] # always returns a tuple
        return max([dgb_latest(self.delegateable)] + map(dgb_latest, self.delegateable.children))
    
    latest_comment = property(_latest_comment)