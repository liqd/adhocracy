import cgi
from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.model.forms as forms
from adhocracy.lib.tiles.proposal_tiles import ProposalTile

log = logging.getLogger(__name__)

class ProposalCreateForm(formencode.Schema):
    allow_extra_fields = True
    label = validators.String(max=255, min=4, not_empty=True)
    text = validators.String(max=10000, min=4, not_empty=True)
    #issue = forms.ValidIssue()
    
class ProposalEditForm(formencode.Schema):
    allow_extra_fields = True
    label = validators.String(max=255, min=4, not_empty=True)
    issue = forms.ValidIssue(not_empty=True)

class ProposalDecisionsFilterForm(formencode.Schema):
    allow_extra_fields = True
    result = validators.Int(not_empty=False, if_empty=None, min=-1, max=1)


class ProposalController(BaseController):
    
    
    def _parse_relations(self, proposal=None):
        types_val = formencode.ForEach(validators.OneOf(['a', 'd', 'n'], not_empty=True), 
                                              convert_to_list=True)
        proposals_val = formencode.ForEach(forms.ValidProposal(if_empty=None, if_invalid=None), 
                                        convert_to_list=True)
        
        types = types_val.to_python(request.params.getall('rel_type'))
        proposals = proposals_val.to_python(request.params.getall('rel_proposal'))
        if len(types) != len(proposals):
            raise formencode.Invalid("", type, None,
                        error_dict={'rel_error': _("Input error while applying relations.")})
        
        c.relations = dict()
        for type, other in zip(types, proposals):
            if not other:
                continue
            if (proposal and other == proposal) and type in ['a', 'd']:
                raise formencode.Invalid("", type, None,
                        error_dict={
                        'rel_error': _("A proposal cannot have a relation with itself.")})
            if other in c.relations.keys() and c.relations[other] != type:
                raise formencode.Invalid("", type, None,
                        error_dict={
                        'rel_error': _("A proposal can either contradict " + 
                                       "or require another, not both.")})
            c.relations[other] = type
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("proposal.create"))
    def create(self):
        try:
            issue_id = request.params.get('issue')
            c.issue = forms.ValidIssue(not_empty=True).to_python(issue_id)
        except formencode.Invalid:
            h.flash(_("Cannot identify the parent issue."))
            redirect_to("/")
        c.canonicals = ["", ""]
        c.relations = dict() #dict(map(lambda m: (m, 'a'), c.issue.proposals))
        c.proposals = [] #model.Proposal.all(instance=c.instance)
        
        if request.method == "POST":
            try:
                # if the remaining validation fails, we'll still want this to execute
                canonicals_val = formencode.ForEach(validators.String(), 
                                                    convert_to_list=True)
                c.canonicals = filter(lambda p: p != None and len(p), 
                                      canonicals_val.to_python(request.params.getall('canonicals')))
                
                self._parse_relations()
                form_result = ProposalCreateForm().to_python(request.params)
                
                proposal = model.Proposal(c.instance, 
                                          form_result.get("label"),
                                          c.user)
                proposal.issue = c.issue
                model.meta.Session.add(proposal)
                model.meta.Session.flush()
                
                comment = model.Comment(proposal, c.user)
                rev = model.Revision(comment, c.user, 
                                     text.cleanup(form_result.get("text")))
                comment.latest = rev
                proposal.comment = comment
                model.meta.Session.add(comment)
                                
                for c_text in c.canonicals:
                    canonical = model.Comment(proposal, c.user)
                    canonical.canonical = True
                    c_rev = model.Revision(canonical, c.user, 
                                           text.cleanup(c_text))
                    canonical.latest = c_rev
                    model.meta.Session.add(canonical)
                    model.meta.Session.add(c_rev)
                    
                for r_proposal, type in c.relations.items():
                    if type=='a':
                        alternative = model.Alternative(proposal, r_proposal)
                        model.meta.Session.add(alternative)
                    elif type=='d':
                        dependency = model.Dependency(proposal, r_proposal)
                        model.meta.Session.add(dependency)
                
                model.meta.Session.commit()
                # stroh
                
                watchlist.check_watch(proposal)
                
                event.emit(event.T_PROPOSAL_CREATE, c.user, instance=c.instance, 
                           topics=[proposal], proposal=proposal)
            
                redirect_to("/proposal/%s" % str(proposal.id))
            except formencode.Invalid, error:
                defaults = dict(request.params)
                if 'canonicals' in defaults:
                    del defaults['canonicals']
                if 'rel_type' in defaults:
                    del defaults['rel_type']
                if 'rel_proposal' in defaults:
                    del defaults['rel_proposal']
                
                if len(c.canonicals) < 2:
                    c.canonicals += [""] * (2 - len(c.canonicals))
                
                page = render("/proposal/create.html")
                return formencode.htmlfill.render(page, 
                                                  defaults=defaults, 
                                                  errors=error.error_dict,
                                                  force_defaults=False)    
        return render("/proposal/create.html")

    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("proposal.edit")) 
    #@validate(schema=ProposalEditForm(), form="edit", post_only=True)
    def edit(self, id):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        if not democracy.is_proposal_mutable(c.proposal):
            abort(403, h.immutable_proposal_message())
        c.issues = model.Issue.all(instance=c.instance)
        c.proposals = model.Proposal.all(instance=c.instance)
        c.relations = dict()
        for dependency in c.proposal.dependencies:
            if not dependency.delete_time:
                #print "DEP", dependency
                c.relations[dependency.requirement] = 'd'
        for ra in c.proposal.right_alternatives:
            if not ra.delete_time:
                c.relations[ra.left] = 'a'
        for la in c.proposal.left_alternatives:
            if not la.delete_time:
                c.relations[la.right] = 'a'
        for m in c.proposal.issue.proposals:
            if not m in c.relations.keys() and m != c.proposal:
                c.relations[m] = 'n'
        
        if request.method == "POST":
            try:
                self._parse_relations(c.proposal)
                form_result = ProposalEditForm().to_python(request.params)
                               
                c.proposal.label = form_result.get("label")
                c.proposal.issue = form_result.get("issue")
            
                model.meta.Session.add(c.proposal)
                
                now = datetime.utcnow()
                for dependency in c.proposal.dependencies:
                    if dependency.delete_time:
                        continue
                    keep = False
                    for other, type in c.relations.items():
                        if other == dependency.requirement and type == 'd':
                            keep = True
                            del c.relations[other]
                    if not keep:
                        dependency.delete(delete_time=now)
                        model.meta.Session.add(dependency)
                
                for alternative in c.proposal.right_alternatives + \
                                   c.proposal.left_alternatives:
                    if alternative.delete_time:
                        continue
                    keep = False
                    for other, type in c.relations.items():
                        if other == alternative.other(c.proposal) and type == 'a':
                            keep = True
                            del c.relations[other]
                    if not keep:
                        alternative.delete(delete_time=now)
                        model.meta.Session.add(alternative)
                
                for other, type in c.relations.items():
                    if type == 'd':
                        dependency = model.Dependency(c.proposal, other)
                        model.meta.Session.add(dependency)
                    elif type == 'a':
                        alternative = model.Alternative(c.proposal, other)
                        model.meta.Session.add(alternative)
                        
                
                model.meta.Session.commit()
                
                watchlist.check_watch(c.proposal)
            
                event.emit(event.T_PROPOSAL_EDIT, c.user, instance=c.instance, 
                           topics=[c.proposal], proposal=c.proposal)
            
                return redirect_to("/proposal/%s" % str(id))
            except formencode.Invalid, error:
                defaults = dict(request.params)
                del defaults['rel_type']
                del defaults['rel_proposal']
                page = render("/proposal/edit.html")
                return formencode.htmlfill.render(page, 
                                                  defaults=defaults, 
                                                  errors=error.error_dict,
                                                  force_defaults=False)
        return render("/proposal/edit.html")
    
    @RequireInstance
    @ActionProtector(has_permission("proposal.view"))   
    def view(self, id, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, id)     
        h.add_meta("description", text.meta_escape(c.proposal.comment.latest.text, markdown=False)[0:160])
        h.add_meta("dc.title", text.meta_escape(c.proposal.label, markdown=False))
        h.add_meta("dc.date", c.proposal.create_time.strftime("%Y-%m-%d"))
        h.add_meta("dc.author", text.meta_escape(c.proposal.creator.name, markdown=False))
        
        if format == 'rss':
            query = model.meta.Session.query(model.Event)
            query = query.filter(model.Event.topics.contains(c.proposal))
            query = query.order_by(model.Event.time.desc())
            query = query.limit(50)  
            return event.rss_feed(query.all(), _("Proposal: %s") % c.proposal.label,
                                  h.instance_url(c.instance, path="/proposal/%s" % str(c.proposal.id)),
                                  description=_("Activity on the %s proposal") % c.proposal.label)
        
        h.add_rss(_("Proposal: %(proposal)s") % {'proposal': c.proposal.label}, 
                  h.instance_url(c.instance, "/proposal/%s.rss" % c.proposal.id))
        
        c.tile = tiles.proposal.ProposalTile(c.proposal)
        c.issue_tile = tiles.issue.IssueTile(c.proposal.issue)
        
        return render("/proposal/view.html")
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("proposal.delete"))
    def delete(self, id):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        if not democracy.is_proposal_mutable(c.proposal):
            abort(403, h.immutable_proposal_message())
        
        h.flash("Proposal %(proposal)s has been deleted." % {'proposal': c.proposal.label})
        event.emit(event.T_PROPOSAL_DELETE, c.user, instance=c.instance, 
                   topics=[c.proposal], proposal=c.proposal)
        
        c.proposal.delete()
        model.meta.Session.commit()
        redirect_to("/issue/%d" % c.proposal.issue.id)   
    
    @RequireInstance
    @ActionProtector(has_permission("proposal.view")) 
    def votes(self, id):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        filters = dict()
        try:
            filters = ProposalDecisionsFilterForm().to_python(request.params)
        except formencode.Invalid:
            pass
        
        if not c.proposal.poll:
            h.flash(_("%s is not currently in a poll, thus no votes have been counted."))
            redirect_to("/proposal/%s" % str(c.proposal.id))
        
        decisions = democracy.Decision.for_poll(c.proposal.poll)
            
        if filters.get('result'):
            decisions = filter(lambda d: d.result==filters.get('result'), decisions)
            
        c.decisions_pager = NamedPager('decisions', decisions, tiles.decision.proposal_row, 
                                    sorts={_("oldest"): sorting.entity_oldest,
                                           _("newest"): sorting.entity_newest},
                                    default_sort=sorting.entity_newest)
        return render("/proposal/votes.html")

