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


class PollController(BaseController):
    
    @RequireInstance
    @ActionProtector(has_permission("proposal.view"))
    @validate(schema=PollIndexFilter(), post_only=False, on_get=True)
    def index(self):
        scored = democracy.State.critical_proposals(c.instance)
        urgency_sort = sorting.dict_value_sorter(scored)
        proposals = scored.keys()
        
        if hasattr(self, 'form_result'):
            c.filter_made = self.form_result.get('filter_made')
        else:
            c.filter_made = 0
        
        if c.user and c.filter_made == 1:
            proposals = filter(lambda m: not democracy.Decision(c.user, m.poll).is_decided(), proposals)
        elif c.user and c.filter_made == 2:
            proposals = filter(lambda m: not democracy.Decision(c.user, m.poll).is_self_decided(), proposals)
                
        c.proposals_pager = NamedPager('proposals', proposals, tiles.proposal.detail_row, count=4, #list_item,
                                     sorts={_("oldest"): sorting.entity_oldest,
                                            _("newest"): sorting.entity_newest,
                                            _("activity"): sorting.proposal_activity,
                                            _("urgency"): urgency_sort,
                                            _("name"): sorting.delegateable_label},
                                     default_sort=urgency_sort)
        return render("/poll/index.html")
    
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
            poll = model.Poll(c.proposal, c.user)
            model.meta.Session.add(poll)
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
            c.poll.end_poll()
            model.meta.Session.commit()
            event.emit(event.T_PROPOSAL_STATE_REDRAFT, c.user, instance=c.instance, 
                       topics=[c.proposal], proposal=c.proposal)
            redirect_to("/proposal/%s" % str(c.proposal.id))
            
        return render("/poll/abort.html")   
    
        
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

