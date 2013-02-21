from pylons import tmpl_context as c
from pylons.i18n import _

from adhocracy import model
from adhocracy.lib import democracy, helpers as h
from adhocracy.lib.auth import can
from adhocracy.lib.tiles import comment_tiles, proposal_tiles
from adhocracy.lib.tiles.util import render_tile, BaseTile


# A mapping from (current_position, action) to (css_class, title)
# title is a lambda to defer the call of _() until we have a request
action_class = {(model.Vote.YES, model.Vote.YES):
                    ('vote_up active disabled',
                     lambda: _('Your current vote is already pro')),
                (model.Vote.YES, model.Vote.NO):
                    ('vote_down',
                     lambda: _('Click to change you vote to neutral')),
                (model.Vote.ABSTAIN, model.Vote.YES):
                    ('vote_up', lambda: _('Click to vote pro')),
                (model.Vote.ABSTAIN, model.Vote.NO):
                    ('vote_down', lambda: _('Click to vote con')),
                (model.Vote.NO, model.Vote.YES):
                    ('vote_up',
                     lambda: _('Click to change you vote to neutral')),
                (model.Vote.NO, model.Vote.NO):
                    ('vote_down active disabled',
                     lambda: _('Your current vote is already pro'))}


class PollTile(BaseTile):
    '''
    A class to write poll tiles with helper methods for the template.
    '''

    def __init__(self, poll, deactivated=False, widget_class=''):
        self.__state = None
        self.__decision = None
        self.__dnode = None
        self.poll = poll
        self.deactivated = deactivated
        self.widget_size = widget_class
        self.widget_class = 'vote ' + widget_class
        self.widget_class += ' deactivated' if self.deactivated else ''
        score = poll.tally.score
        self.count_class = ('positive' if score > 0 else 'negative' if
                            score < 0 else 'neutral')
        self.display_score = u'0' if score == 0 else u"%+d" % score
        self.html_id = 'poll%s' % poll.id
        self.login_redirect_url = h.login_redirect_url(poll.scope,
                                                       anchor=self.html_id)
        self._calculate_conditions()

    def _calculate_conditions(self):
        self.has_ended = self.poll.has_ended()
        self.can_vote = can.poll.vote(self.poll)
        self.can_show = can.poll.show(self.poll)
        if self.has_ended or self.can_vote:
            self.need_auth = False
            self.need_membership = False
            self.need_else = False
        else:
            self.need_auth = (not self.can_vote and c.user is None)
            self.need_membership = (not self.need_auth and
                                    (c.instance and not
                                     c.user.is_member(c.instance)) and
                                    can.instance.join(c.instance))
            self.need_else = (not self.need_membership)

    def widget_action_attrs(self, position):
        '''
        Generate an url to rate or vote in a poll.

        *position*
            The value of the vote. +1 = Pro, 0 = Neutral, +1 = Con.
            For *type_* 'rate' it's only +1 and -1
        '''

        if position not in [model.Vote.YES, model.Vote.NO]:
            raise ValueError(('position "%s" not supported by widget. Use'
                              'model.Vote.YES or model.Vote.NO.') % position)
        title = ''
        url = ''
        klass = 'vote_up' if position == model.Vote.YES else 'vote_down'
        if self.can_vote:
            url = self._rate_url(self.poll, position)
            klass, title_func = action_class[(self.current_position, position)]
            title = title_func()
        elif self.has_ended:
            url = self.votes_listing_url
            title = _('Voting has ended. Click to view the list of votes')
        elif self.need_auth:
            url = self.login_redirect_url
            title = _('Please login or register to vote.')
        elif self.need_membership:
            url = '#%s' % self.html_id  # FIXME: implement join and redirect?
            title = _('Please join the instance "%s" to vote.')
        elif self.need_else:
            # We can't figure out what to do, so no options to vote
            url = self.votes_listing_url
            title = _('Click to see the list of votes')
        else:
            raise ValueError(
                'Dunno how this could happen. A bug apparently :)')

        return {'title': title, 'url': url, 'class': klass}

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
        Returns: the decision of the current user
        This will be *model.Vote.YES*, *model.Vote.ABSTAIN* or
        *model.Vote.NO*. If there is no current user, it will
        return *model.Vote.ABSTAIN*.
        '''
        result = None
        decision = self.decision
        if decision:
            result = decision.result
        if result is None:
            result = model.Vote.ABSTAIN
        return result

    def _rate_url(self, poll, position):
        params = {'url': h.entity_url(poll, member='rate'),
                  'token_param': h.url_token(),
                  'position': position,
                  'cls': self.widget_size}
        return ("%(url)s?position=%(position)d&"
                "%(token_param)s&cls=%(cls)s") % params

    @property
    def votes_listing_url(self):
        return h.entity_url(self.poll, member="votes")


def booth(poll):
    return render_tile('/poll/tiles.html', 'booth',
                       PollTile(poll), poll=poll, user=c.user, cached=True)


def row(poll):
    return render_tile('/poll/tiles.html', 'row',
                       PollTile(poll), poll=poll, user=c.user, cached=True)


def widget(poll, cls='', deactivated=False, delegate_url=None):
    '''
    FIXME: fix caching. Poll objects don't change. Tallies are
    generated for every vote. Ask @pudo about this.

    Render a rating widget for an :class:`adhocracy.model.poll.Poll`.
    It is rendered based on the permission of the current user to
    vote for the poll.

    TODO: Add support for helpful tooltips for the voting buttons.

    *cls* (str)
        The type that will be rendered as css class in the widget.
        By default it is a small widget. Using 'big' will render a
        big one.
    *deactivated*
        Render the widget deactivated which does not show vote buttons
        or the current position of the user, but still the vote count.
    *delegate_url* (unicode or None)
        An URL if a delegate button should be shown beside the vote
        widget. If *None* (default) no button will be shown.
    '''
    t = PollTile(poll, deactivated, widget_class=cls)
    return render_tile('/poll/tiles.html', 'widget',
                       t, poll=poll, user=c.user, widget_class=cls,
                       delegate_url=delegate_url, deactivated=deactivated,
                       cached=True)


def header(poll, active=''):
    if isinstance(poll.subject, model.Comment):
        return comment_tiles.header(poll.subject, active=active)
    elif isinstance(poll.scope, model.Proposal):
        return proposal_tiles.header(poll.scope, active=active)
