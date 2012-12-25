from pylons import tmpl_context as c

from adhocracy.lib.tiles.util import BaseTile


from adhocracy.lib import democracy


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
