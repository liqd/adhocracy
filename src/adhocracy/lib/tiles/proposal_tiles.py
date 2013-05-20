from datetime import datetime, timedelta
from pylons import tmpl_context as c
from adhocracy.lib.helpers.proposal_helper import monitor_clicks

from adhocracy.lib.auth import authorization
from adhocracy.lib.democracy import Decision
from adhocracy.lib.tiles.util import render_tile
from adhocracy.lib.tiles.delegateable_tiles import DelegateableTile



class ProposalTile(DelegateableTile):

    def __init__(self, proposal, loop=None, sort=None):
        self.proposal = proposal
        self.loop = loop
        self.sort = sort
        self.__poll = None
        self.__decision = None
        self.__num_principals = None
        self.__comment_tile = None
        DelegateableTile.__init__(self, proposal)

    @property
    def fresh(self):
        return ((datetime.utcnow() - self.proposal.create_time) <
                timedelta(hours=36))

    @property
    def poll(self):
        if not self.__poll:
            self.__poll = self.proposal.adopt_poll
        return self.__poll

    @property
    def delegates(self):
        agents = []
        if not c.user:
            return []
        for delegation in self.dnode.outbound():
            agents.append(delegation.agent)
        return set(agents)

    @property
    def num_principals(self):
        if self.__num_principals is None:
            principals = set(map(lambda d: d.principal,
                                 self.dnode.transitive_inbound()))
            if self.poll:
                principals = filter(
                    lambda p: not Decision(p, self.poll).is_self_decided(),
                    principals)
            self.__num_principals = len(principals)
        return self.__num_principals


def row(proposal, **kwargs):
    global_admin = authorization.has('global.admin')
    if not proposal:
        return ""
    # if adhocracy.monitor_clicks is set, caching must be turned off
    # otherwise the index of the clicked linked is cached and does not change
    # with different sorts
    return render_tile('/proposal/tiles.html', 'row', ProposalTile(proposal, kwargs.get('loop'), kwargs.get('sort')),
                       proposal=proposal, cached=not monitor_clicks(),
                       badgesglobal_admin=global_admin)


def header(proposal, tile=None, active='goal'):
    if tile is None:
        tile = ProposalTile(proposal)
    return render_tile('/proposal/tiles.html', 'header', tile,
                       proposal=proposal, active=active)


def panel(proposal, tile):
    return render_tile('/proposal/tiles.html', 'panel', tile,
                       proposal=proposal, cached=True)


def sidebar(proposal, tile=None):
    if tile is None:
        tile = ProposalTile(proposal)
    return render_tile('/proposal/tiles.html', 'sidebar', tile,
                       proposal=proposal)
