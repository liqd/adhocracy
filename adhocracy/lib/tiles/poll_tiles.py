from pylons import tmpl_context as c

from adhocracy import model
from adhocracy.lib import democracy
from adhocracy.lib.tiles import comment_tiles, proposal_tiles
from adhocracy.lib.tiles.util import render_tile, BaseTile


class PollTile(BaseTile):

    def __init__(self, poll):
        self.poll = poll
        self.__state = None
        self.__decision = None
        self.__dnode = None

    @property
    def state(self):
        if not self.__state:
            self.__state = democracy.State(self.poll.proposal, poll=self.poll)
        return self.__state

    @property
    def dnode(self):
        if not self.__dnode:
            self.__dnode = democracy.DelegationNode(c.user, self.poll.scope)
        return self.__dnode

    @property
    def decision(self):
        if not self.__decision and c.user:
            self.__decision = democracy.Decision(c.user, self.poll)
        return self.__decision

    @property
    def delegates(self):
        agents = []
        if not c.user:
            return []
        for delegation in self.dnode.outbound():
            agents.append(delegation.agent)
        return set(agents)

    def delegates_result(self, result):
        agents = []
        for agent in self.delegates:
            decision = democracy.Decision(agent, self.poll)
            if decision.is_decided() and decision.result == result:
                agents.append(agent)
        return agents

    @property
    def result_affirm(self):
        return round(self.poll.tally.rel_for * 100.0, 1)

    @property
    def result_dissent(self):
        return round(self.poll.tally.rel_against * 100.0, 1)


def booth(poll):
    return render_tile('/poll/tiles.html', 'booth',
                        PollTile(poll), poll=poll, user=c.user, cached=True)


def header(poll, active=''):
    if isinstance(poll.subject, model.Comment):
        return comment_tiles.header(poll.subject, active=active)
    elif isinstance(poll.scope, model.Proposal):
        return proposal_tiles.header(poll.scope, active=active)
