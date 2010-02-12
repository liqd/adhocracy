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
    orientation = validators.Int(min=vote.Vote.NO, max=vote.Vote.YES, not_empty=True)


class PollController(BaseController):
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("poll.create")) 
    def create(self, id):
        # TODO "id" really shouldn't be an URL part but a request parameter. 
        c.proposal = get_entity_or_abort(model.Proposal, id)
        
        tile = ProposalTile(c.proposal)
        if not tile.can_begin_poll:
            abort(403, _("The poll cannot be started either because there are "
                       + "no provisions or a poll has already started."))
        
        if request.method == "POST":
            model.Poll.create(c.proposal, c.user, model.Poll.ADOPT)
            model.meta.Session.commit()
            event.emit(event.T_PROPOSAL_STATE_VOTING, c.user, instance=c.instance, 
                       topics=[c.proposal], proposal=c.proposal)
            redirect_to("/proposal/%s" % str(c.proposal.id))
        return render("/poll/create.html")
                
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("poll.abort")) 
    def abort(self, id):
        c.poll = get_entity_or_abort(model.Poll, id)
        c.proposal = c.poll.proposal
        tile = PollTile(c.poll)
        if not c.poll or c.poll.has_ended():
            abort(404, _("The proposal is not undergoing a poll."))
        
        if not tile.can_end_poll:
            abort(403, _("The poll cannot be canceled because it has met " 
                         + "some of the adoption criteria."))
        
        if request.method == "POST":
            c.poll.end()
            model.meta.Session.commit()
            event.emit(event.T_PROPOSAL_STATE_REDRAFT, c.user, instance=c.instance, 
                       topics=[c.proposal], proposal=c.proposal)
            redirect_to("/proposal/%s" % str(c.proposal.id))
            
        return render("/poll/abort.html")   
    
    @RequireInstance
    @ActionProtector(has_permission("vote.cast"))
    def rate(self, id):
        pass
    
        
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("vote.cast"))
    @validate(schema=PollVoteForm(), form="bad_request", post_only=False, on_get=True)
    def vote(self, id):
        c.poll = self._get_open_poll(id)
        
        if not h.has_permission("vote.cast"):
            h.flash(_("You have no voting rights."))
            redirect_to("/proposal/%s" % str(id))
            
        orientation = self.form_result.get("orientation")
        votes = democracy.Decision(c.user, c.poll).make(orientation)
        for vote in votes:
            event.emit(event.T_VOTE_CAST, vote.user, instance=c.instance, 
                       topics=[c.poll.proposal], vote=vote, poll=c.poll)
        redirect_to("/proposal/%s" % str(c.poll.proposal.id))
    
        
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
            
        c.decisions_pager = NamedPager('decisions', decisions, tiles.decision.proposal_row, 
                                    sorts={_("oldest"): sorting.entity_oldest,
                                           _("newest"): sorting.entity_newest},
                                    default_sort=sorting.entity_newest)
        return render("/poll/votes.html")   
    
    def _get_open_poll(self, id):
        poll = get_entity_or_abort(model.Poll, id)
        if poll.has_ended():
            abort(404, _("The proposal is not undergoing a poll."))
        return poll          

