import logging
from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *
from adhocracy.lib.tiles.poll_tiles import PollTile
from adhocracy.lib.tiles.proposal_tiles import ProposalTile

log = logging.getLogger(__name__)

class PollIndexFilter(formencode.Schema):
    allow_extra_fields = True
    filter_made = validators.Int(not_empty=False, if_empty=1, if_missing=1, if_invalid=1, min=0, max=2)

class PollDecisionsFilterForm(formencode.Schema):
    allow_extra_fields = True
    result = validators.Int(not_empty=False, if_empty=None, min=-1, max=1)
    
class PollVoteForm(formencode.Schema):
    allow_extra_fields = True
    position = validators.Int(min=model.Vote.NO, max=model.Vote.YES, not_empty=True)


class PollController(BaseController):
    
    def index(self, id):
        return self.not_implemented()
    
        
    def new(self, id):
        return self.not_implemented()
    
    
    def create(self, id):
        return self.not_implemented()
    
        
    def edit(self, id):
        return self.not_implemented()
        
    
    def update(self, id):
        return self.not_implemented()  
    
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("vote.cast"))
    @validate(schema=PollVoteForm(), form="bad_request", post_only=False, on_get=True)
    def vote(self, id, format='html'):
        c.poll = self._get_open_poll(id)
        decision = democracy.Decision(c.user, c.poll)
        previous_result = decision.result
        votes = decision.make(self.form_result.get("position"))
        if c.poll.action != model.Poll.RATE:
            for vote in votes:
                event.emit(event.T_VOTE_CAST, vote.user, instance=c.instance, 
                           topics=[c.poll.scope], vote=vote, poll=c.poll)
        
        if format == 'json':
            tally = model.Tally.create_from_poll(c.poll)
            model.meta.Session.commit()
            return render_json(dict(decision=decision,
                                    score=tally.score))
        redirect_to(h.entity_url(c.poll.subject))
    
        
    @RequireInstance
    @ActionProtector(has_permission("proposal.view")) 
    def votes(self, id):
        c.poll = get_entity_or_abort(model.Poll, id)
        filters = dict()
        try:
            filters = PollDecisionsFilterForm().to_python(request.params)
        except formencode.Invalid:
            pass
        
        if not c.poll:
            abort(404, _("%s is not currently in a poll, thus no votes have been counted."))
        
        c.tile = tiles.poll.PollTile(c.poll)
        
        decisions = democracy.Decision.for_poll(c.poll)
            
        if filters.get('result'):
            decisions = filter(lambda d: d.result==filters.get('result'), decisions)
            
        c.decisions_pager = pager.scope_descisions(decisions)
        return render("/poll/votes.html")  
        
    
    @ActionProtector(has_permission("poll.abort"))
    def ask_delete(self, id):
        c.poll = self._get_open_poll(id)
        if not c.poll.can_end():
            abort(403, _("The poll cannot be canceled because it has met " +
                         "some of the adoption criteria."))
        return render('/poll/ask_delete.html')
    
    
    @ActionProtector(has_permission("poll.abort"))    
    def delete(self, id):
        c.poll = self._get_open_poll(id)
        if not c.poll.can_end():
            abort(403, _("The poll cannot be canceled because it has met " +
                         "some of the adoption criteria."))
        c.poll.end()
        model.meta.Session.commit()
        event.emit(event.T_PROPOSAL_STATE_REDRAFT, c.user, instance=c.instance, 
                   topics=[c.poll.scope], proposal=c.poll.scope, poll=c.poll)
        redirect_to(h.entity_url(c.poll.subject))
    
    
    def _get_open_poll(self, id):
        poll = get_entity_or_abort(model.Poll, id)
        if poll.has_ended():
            abort(404, _("The proposal is not undergoing a poll."))
        return poll          

