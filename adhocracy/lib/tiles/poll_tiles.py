from pylons import tmpl_context as c

from adhocracy import model
from adhocracy.lib import democracy, helpers as h
from adhocracy.lib.tiles import comment_tiles, proposal_tiles
from adhocracy.lib.tiles.util import render_tile, BaseTile


class PollTile(BaseTile):
    '''
    A class to write poll tiles with helper methods for the template.
    '''
    RATE = 0
    VOTE = 1

    def __init__(self, poll, deactivated=False, need_auth=False):
        self.poll = poll
        self.deactivated = deactivated
        self.need_auth = need_auth
        self.__state = None
        self.__decision = None
        self.__dnode = None
        self.html_id = 'poll%s' % poll.id
        score = poll.tally.score
        self.count_class = ('positive' if score > 0 else 'negative' if
                            score < 0 else 'neutral')
        self.display_score = u'0' if score == 0 else u"%+d" % score
        self.login_redirect_url = h.login_redirect_url(poll.scope,
                                                       anchor=self.html_id)

    def action_url(self, position, type_=RATE):
        '''
        Generate an url to rate or vote in a poll.

        *position*
            The value of the vote. +1 = Pro, 0 = Neutral, +1 = Con.
            For *type_* 'rate' it's only +1 and -1
        *type_*
            The type to use the poll. Either ``RATE`` (default)
            or ``VOTE``. ``RATE`` is a three step variant
            where the user steps from -1 to 0 to +1 or the other
            way around. ``VOTE`` will directly set the selected position
            and is NotImplemented.
        '''
        if self.need_auth:
            return self.login_redirect_url
        elif self.deactivated:
            return ''
        if type_ == self.RATE:
            if position == 0:
                raise ValueError('Rating neutral is not possible')
            return self._rate_url(self.poll, 1)
        elif type_ == self.VOTE:
            raise NotImplemented('PollTile does not support '
                                 'action_url for voting')
        else:
            raise ValueError('Unsupported type_, use VOTE or RATE')

    @property
    def deactivated_class(self):
        return 'deactivated' if self.deactivated else ''

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

    @property
    def current_position(self):
        '''
        Return the decision of the current user
        This will be
        *None*
            if there is no user
        *-1, 0 or 1 (int)*
            against, abstain/not voted and affirmation
        '''
        decision = self.decision
        if decision:
            return decision.result

    def _rate_url(self, poll, position):
        params = {'url': h.entity_url(poll, member='rate'),
                  'token_param': h.url_token(),
                  'position': position}
        return "%(url)s?position=%(position)s&%(token_param)s" % params


def booth(poll):
    return render_tile('/poll/tiles.html', 'booth',
                        PollTile(poll), poll=poll, user=c.user, cached=True)


def widget(poll, cls='', deactivated=False, need_auth=False):
    '''
    FIXME: fix caching. Poll objects don't change. Tallies are
    generated for every vote. Ask @pudo about this.

    Render a rating widget for an :class:`adhocracy.model.poll.Poll`
    TODO: Add support for helpful tooltips for the voting buttons.

    *cls* (str)
        The type that will be rendered as css class in the widget.
        By default it is a small widget. Using 'big' will render a
        big one.
    *deactivated*
        Render the widget deactivated which does not show vote buttons
        or the current position of the user, but still the vote count.
    *need_auth*
       Render the widget in a semi-active state where users will be
       redirected to the login form. TODO: Implement useful tooltips.
    '''
    t = PollTile(poll, deactivated, need_auth)
    return render_tile('/poll/tiles.html', 'widget',
                       t, poll=poll, user=c.user, cls=cls,
                       deactivated=deactivated, need_auth=need_auth,
                       cached=True)


def header(poll, active=''):
    if isinstance(poll.subject, model.Comment):
        return comment_tiles.header(poll.subject, active=active)
    elif isinstance(poll.scope, model.Proposal):
        return proposal_tiles.header(poll.scope, active=active)
