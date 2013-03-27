import logging

import formencode
from formencode import validators

from pylons import tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons.decorators import validate
from pylons.i18n import _


from adhocracy import model
from adhocracy.lib import democracy, event, helpers as h, pager, tiles
from adhocracy.lib.auth import require
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib.base import BaseController
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib.templating import render, render_def, render_json
from adhocracy.lib.templating import ret_abort, ret_success
from adhocracy.lib.util import get_entity_or_abort


log = logging.getLogger(__name__)


class PollVotesFilterForm(formencode.Schema):
    allow_extra_fields = True
    result = validators.Int(not_empty=False, if_empty=None, if_missing=None,
                            min=model.Vote.NO, max=model.Vote.YES)


class PollVoteForm(formencode.Schema):
    allow_extra_fields = True
    position = validators.Int(min=model.Vote.NO, max=model.Vote.YES,
                              not_empty=True)


class PollController(BaseController):

    def index(self, format='html'):
        return self.not_implemented(format=format)

    def new(self, id, format='html'):
        return self.not_implemented(format=format)

    def create(self, id, format='html'):
        return self.not_implemented(format=format)

    def edit(self, id, format='html'):
        return self.not_implemented(format=format)

    def update(self, id, format='html'):
        return self.not_implemented(format=format)

    @RequireInstance
    def show(self, id, format='html'):
        poll = get_entity_or_abort(model.Poll, id)
        require.poll.show(poll)

        if format == 'json':
            return render_json(poll)

        return self.not_implemented(format=format)

    @RequireInstance
    @RequireInternalRequest()
    @validate(schema=PollVoteForm(), form="bad_request", post_only=False,
              on_get=True)
    def vote(self, id, format):
        c.poll = self._get_open_poll(id)
        if c.poll.action != model.Poll.ADOPT:
            abort(400, _("This is not an adoption poll."))
        require.poll.vote(c.poll)
        decision = democracy.Decision(c.user, c.poll)
        votes = decision.make(self.form_result.get("position"))

        for vote in votes:
            event.emit(event.T_VOTE_CAST, vote.user, instance=c.instance,
                       topics=[c.poll.scope], vote=vote, poll=c.poll)
        model.meta.Session.commit()

        if format == 'json':
            return render_json(dict(decision=decision,
                                    score=c.poll.tally.score))

        redirect(h.entity_url(c.poll.subject))

    @RequireInstance
    @RequireInternalRequest()
    @validate(schema=PollVoteForm(), form="bad_request",
              post_only=False, on_get=True)
    def rate(self, id, format):
        # rating is like polling but steps via abstention, i.e. if you have
        # first voted "for", rating will first go to "abstain" and only
        # then produce "against"-
        c.poll = self._get_open_poll(id)
        if c.poll.action not in [model.Poll.RATE, model.Poll.SELECT]:
            abort(400, _("This is not a rating poll."))
        require.poll.vote(c.poll)

        decision = democracy.Decision(c.user, c.poll)
        old = decision.result
        new = self.form_result.get("position")
        positions = {(model.Vote.YES, model.Vote.YES): model.Vote.YES,
                     (model.Vote.ABSTAIN, model.Vote.YES): model.Vote.YES,
                     (model.Vote.NO, model.Vote.YES): model.Vote.ABSTAIN,
                     (model.Vote.YES, model.Vote.NO): model.Vote.ABSTAIN,
                     (model.Vote.ABSTAIN, model.Vote.NO): model.Vote.NO,
                     (model.Vote.NO, model.Vote.NO): model.Vote.NO}
        position = positions.get((old, new), new)
        votes = decision.make(position)
        tally = model.Tally.create_from_poll(c.poll)
        event_type = {model.Poll.RATE: event.T_RATING_CAST,
                      model.Poll.SELECT: event.T_SELECT_VARIANT
                      }.get(c.poll.action)
        for vote in votes:
            event.emit(event_type, vote.user, instance=c.instance,
                       topics=[c.poll.scope], vote=vote, poll=c.poll)
        model.meta.Session.commit()

        if format == 'json':
            return render_json(dict(decision=decision,
                                    tally=tally.to_dict()))

        if format == 'overlay':
            return self.widget(id, format=self.form_result.get('cls'))

        if c.poll.action == model.Poll.SELECT:
            redirect(h.entity_url(c.poll.selection))

        redirect(h.entity_url(c.poll.subject))

    @RequireInstance
    @validate(schema=PollVotesFilterForm(), post_only=False, on_get=True)
    def votes(self, id, format='html'):
        c.poll = get_entity_or_abort(model.Poll, id)

        # cover over data inconsistency because of a bug where pages (norms)
        # where deleted when a proposal was deleted.
        # Fixes http://trac.adhocracy.de/ticket/262
        if (c.poll.action == model.Poll.SELECT and
                c.poll.selection is None):
            logmsg = ('Poll: "%s" is a model.Poll.rate poll, which should '
                      'have a selection, but the selection is None. Subject '
                      'of the Poll is %s') % (c.poll, c.poll.subject)
            log.error(logmsg)
            raise abort(404)

        require.poll.show(c.poll)
        decisions = democracy.Decision.for_poll(c.poll)
        if (hasattr(self, 'form_result') and
                self.form_result.get('result') != None):
            result_form = self.form_result.get('result')
            decisions = filter(lambda d: d.result == result_form, decisions)
        c.decisions_pager = pager.scope_decisions(decisions)

        if format == 'overlay':
            return render_def('/pager.html', 'overlay_pager',
                              pager=c.decisions_pager,
                              render_facets=False)

        if format == 'json':
            return render_json(c.decisions_pager)

        return render("/poll/votes.html")

    def ask_delete(self, id):
        c.poll = self._get_open_poll(id)
        require.poll.delete(c.poll)
        return render('/poll/ask_delete.html')

    def delete(self, id, format):
        c.poll = self._get_open_poll(id)
        require.poll.delete(c.poll)
        c.poll.end()
        model.meta.Session.commit()
        event.emit(event.T_PROPOSAL_STATE_REDRAFT, c.user, instance=c.instance,
                   topics=[c.poll.scope], proposal=c.poll.scope, poll=c.poll)
        return ret_success(message=_("The poll has ended."),
                           entity=c.poll.subject)

    def _get_open_poll(self, id):
        poll = get_entity_or_abort(model.Poll, id)
        if poll.has_ended():
            return ret_abort(_("The proposal is not undergoing a poll."),
                             code=404)
        return poll

    def widget(self, id, format):
        if format is None:
            format = ''
        poll = get_entity_or_abort(model.Poll, id)
        return tiles.poll.widget(poll, cls=format)
