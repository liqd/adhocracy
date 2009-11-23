import cgi
from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.model.forms as forms
from adhocracy.lib.tiles.motion_tiles import MotionTile

log = logging.getLogger(__name__)

class MotionCreateForm(formencode.Schema):
    allow_extra_fields = True
    label = validators.String(max=255, min=4, not_empty=True)
    text = validators.String(max=10000, min=4, not_empty=True)
    #issue = forms.ValidIssue()
    
class MotionEditForm(formencode.Schema):
    allow_extra_fields = True
    label = validators.String(max=255, min=4, not_empty=True)
    issue = forms.ValidIssue(not_empty=True)

class MotionDecisionsFilterForm(formencode.Schema):
    allow_extra_fields = True
    result = validators.Int(not_empty=False, if_empty=None, min=-1, max=1)


class MotionController(BaseController):
    
    
    def _parse_relations(self, motion=None):
        types_val = formencode.ForEach(validators.OneOf(['a', 'd', 'n'], not_empty=True), 
                                              convert_to_list=True)
        motions_val = formencode.ForEach(forms.ValidMotion(if_empty=None, if_invalid=None), 
                                        convert_to_list=True)
        
        #print "REL_MOTIONS", request.params.getall('rel_motion')
        
        types = types_val.to_python(request.params.getall('rel_type'))
        motions = motions_val.to_python(request.params.getall('rel_motion'))
        if len(types) != len(motions):
            raise formencode.Invalid("", type, None,
                        error_dict={'rel_error': _("Input error while applying relations.")})
        
        #print "MOTIONS ", motions
        
        c.relations = dict()
        for type, other in zip(types, motions):
            if not other:
                continue
            if (motion and other == motion) and type in ['a', 'd']:
                raise formencode.Invalid("", type, None,
                        error_dict={
                        'rel_error': _("A motion cannot have a relation with itself.")})
            if other in c.relations.keys() and c.relations[other] != type:
                raise formencode.Invalid("", type, None,
                        error_dict={
                        'rel_error': _("A motion can either contradict " + 
                                       "or require another, not both.")})
            c.relations[other] = type
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("motion.create"))
    #@validate(schema=MotionCreateForm(), form="create", post_only=True)
    def create(self):
        auth.require_motion_perm(None, 'comment.create')
        try:
            c.issue = forms.ValidIssue(not_empty=True).to_python(request.params.get('issue'))
        except formencode.Invalid:
            h.flash(_("Cannot identify the parent issue."))
            redirect_to("/")
        c.canonicals = ["", ""]
        c.relations = dict(map(lambda m: (m, 'a'), c.issue.motions))
        c.motions = model.Motion.all(instance=c.instance)
        
        if request.method == "POST":
            try:
                # if the remaining validation fails, we'll still want this to execute
                canonicals_val = formencode.ForEach(validators.String(), 
                                                    convert_to_list=True)
                c.canonicals = filter(lambda p: p != None and len(p), 
                                      canonicals_val.to_python(request.params.getall('canonicals')))
                
                self._parse_relations()
                form_result = MotionCreateForm().to_python(request.params)
                motion = model.Motion(c.instance, 
                                      form_result.get("label"),
                                      c.user)
                motion.issue = c.issue
                comment = model.Comment(motion, c.user)
                rev = model.Revision(comment, c.user, 
                                     text.cleanup(form_result.get("text")))
                comment.latest = rev
                model.meta.Session.add(motion)
                model.meta.Session.add(comment)
                model.meta.Session.add(rev)
                
                for c_text in c.canonicals:
                    canonical = model.Comment(motion, c.user)
                    canonical.canonical = True
                    c_rev = model.Revision(canonical, c.user, 
                                           text.cleanup(c_text))
                    canonical.latest = c_rev
                    model.meta.Session.add(canonical)
                    model.meta.Session.add(c_rev)
                    
                for r_motion, type in c.relations.items():
                    if type=='a':
                        alternative = model.Alternative(motion, r_motion)
                        model.meta.Session.add(alternative)
                    elif type=='d':
                        dependency = model.Dependency(motion, r_motion)
                        model.meta.Session.add(dependency)
                
                model.meta.Session.commit()
                motion.comment = comment
                model.meta.Session.add(motion)
                model.meta.Session.commit()
                model.meta.Session.refresh(rev)
                
                watchlist.check_watch(motion)
                
                event.emit(event.T_MOTION_CREATE, c.user, scopes=[c.instance], 
                           topics=[motion, motion.issue, c.instance], motion=motion)
            
                redirect_to("/motion/%s" % str(motion.id))
            except formencode.Invalid, error:
                defaults = dict(request.params)
                del defaults['canonicals']
                del defaults['rel_type']
                del defaults['rel_motion']
                
                if len(c.canonicals) < 2:
                    c.canonicals += [""] * (2 - len(c.canonicals))
                
                page = render("/motion/create.html")
                return formencode.htmlfill.render(page, 
                                                  defaults=defaults, 
                                                  errors=error.error_dict,
                                                  force_defaults=False)    
        return render("/motion/create.html")

    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("motion.edit")) 
    #@validate(schema=MotionEditForm(), form="edit", post_only=True)
    def edit(self, id):
        self._parse_motion_id(id)
        auth.require_motion_perm(c.motion, 'comment.edit')
        c.issues = model.Issue.all(instance=c.instance)
        c.motions = model.Motion.all(instance=c.instance)
        c.relations = dict()
        for dependency in c.motion.dependencies:
            if not dependency.delete_time:
                #print "DEP", dependency
                c.relations[dependency.requirement] = 'd'
        for ra in c.motion.right_alternatives:
            if not ra.delete_time:
                c.relations[ra.left] = 'a'
        for la in c.motion.left_alternatives:
            if not la.delete_time:
                c.relations[la.right] = 'a'
        for m in c.motion.issue.motions:
            if not m in c.relations.keys() and m != c.motion:
                c.relations[m] = 'n'
        
        if request.method == "POST":
            try:
                self._parse_relations(c.motion)
                form_result = MotionEditForm().to_python(request.params)
                               
                c.motion.label = form_result.get("label")
                c.motion.issue = form_result.get("issue")
            
                model.meta.Session.add(c.motion)
                
                now = datetime.now()
                for dependency in c.motion.dependencies:
                    if dependency.delete_time:
                        continue
                    keep = False
                    for other, type in c.relations.items():
                        if other == dependency.requirement and type == 'd':
                            keep = True
                            del c.relations[other]
                    if not keep:
                        dependency.delete_time = now
                        model.meta.Session.add(dependency)
                
                for alternative in c.motion.right_alternatives + \
                                   c.motion.left_alternatives:
                    if alternative.delete_time:
                        continue
                    keep = False
                    for other, type in c.relations.items():
                        if other == alternative.other(c.motion) and type == 'a':
                            keep = True
                            del c.relations[other]
                    if not keep:
                        alternative.delete_time = now
                        model.meta.Session.add(alternative)
                
                for other, type in c.relations.items():
                    if type == 'd':
                        dependency = model.Dependency(c.motion, other)
                        model.meta.Session.add(dependency)
                    elif type == 'a':
                        alternative = model.Alternative(c.motion, other)
                        model.meta.Session.add(alternative)
                        
                
                model.meta.Session.commit()
                
                watchlist.check_watch(c.motion)
            
                event.emit(event.T_MOTION_EDIT, c.user, scopes=[c.instance], 
                           topics=[c.motion, c.motion.issue], motion=c.motion)
            
                return redirect_to("/motion/%s" % str(id))
            except formencode.Invalid, error:
                defaults = dict(request.params)
                del defaults['rel_type']
                del defaults['rel_motion']
                page = render("/motion/edit.html")
                return formencode.htmlfill.render(page, 
                                                  defaults=defaults, 
                                                  errors=error.error_dict,
                                                  force_defaults=False)
        return render("/motion/edit.html")
    
    @RequireInstance
    @ActionProtector(has_permission("motion.view"))   
    def view(self, id, format='html'):
        self._parse_motion_id(id)     
        
        h.add_meta("description", "")
        h.add_meta("dc.title", text.meta_escape(c.motion.label, markdown=False))
        h.add_meta("dc.date", c.motion.create_time.strftime("%Y-%m-%d"))
        h.add_meta("dc.author", text.meta_escape(c.motion.creator.name, markdown=False))
        
        if format == 'rss':
            events = event.q.run(event.q.topic(c.motion))
            return event.rss_feed(events, _("Motion: %s") % c.motion.label,
                                  h.instance_url(c.instance, path="/motion/%s" % str(c.motion.id)),
                                  description=_("Activity on the %s motion") % c.motion.label)
        
        h.add_rss(_("Motion: %(motion)s") % {'motion': c.motion.label}, 
                  h.instance_url(c.instance, "/motion/%s.rss" % c.motion.id))
        
        c.tile = tiles.motion.MotionTile(c.motion)
        c.issue_tile = tiles.issue.IssueTile(c.motion.issue)
        
        return render("/motion/view.html")
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("motion.delete"))
    def delete(self, id):
        self._parse_motion_id(id)
        auth.require_motion_perm(c.motion, 'comment.delete')
        parent = c.instance.root
        if len(c.motion.parents):
            parent = c.motion.parents[0]
        h.flash("Motion %(motion)s has been deleted." % {'motion': c.motion.label})
        
        event.emit(event.T_MOTION_DELETE, c.user, scopes=[c.instance], 
                   topics=[c.motion, c.motion.issue, c.instance], motion=c.motion)
        
        c.motion.delete_time = datetime.now()
        model.meta.Session.add(c.motion)
        model.meta.Session.commit()
        redirect_to("/category/%s" % str(parent.id))   
    
    @RequireInstance
    @ActionProtector(has_permission("motion.view")) 
    def votes(self, id):
        self._parse_motion_id(id)
        filters = dict()
        try:
            filters = MotionDecisionsFilterForm().to_python(request.params)
        except formencode.Invalid:
            pass
        
        if not c.motion.poll:
            h.flash(_("%s is not currently in a poll, thus no votes have been counted."))
            redirect_to("/motion/%s" % str(c.motion.id))
        
        decisions = democracy.Decision.for_poll(c.motion.poll)
            
        if filters.get('result'):
            decisions = filter(lambda d: d.result==filters.get('result'), decisions)
            
        c.decisions_pager = NamedPager('decisions', decisions, tiles.decision.motion_row, 
                                    sorts={_("oldest"): sorting.entity_oldest,
                                           _("newest"): sorting.entity_newest},
                                    default_sort=sorting.entity_newest)
        return render("/motion/votes.html")

