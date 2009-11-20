import logging
from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *
from adhocracy.lib.tiles.motion_tiles import MotionTile

log = logging.getLogger(__name__)

class PollIndexFilter(formencode.Schema):
    filter_made = validators.Int(not_empty=False, if_empty=1, if_missing=1, if_invalid=1, min=0, max=2)

class PollController(BaseController):
    
    @RequireInstance
    @ActionProtector(has_permission("motion.view"))
    @validate(schema=PollIndexFilter(), post_only=False, on_get=True)
    def index(self):
        scored = democracy.State.critical_motions(c.instance)
        urgency_sort = sorting.dict_value_sorter(scored)
        motions = scored.keys()
        
        c.filter_made = self.form_result.get('filter_made')
        if c.user and c.filter_made == 1:
            motions = filter(lambda m: not democracy.Decision(c.user, m.poll).made(), motions)
        elif c.user and c.filter_made == 2:
            motions = filter(lambda m: not democracy.Decision(c.user, m.poll).self_made(), motions)
                
        c.motions_pager = NamedPager('motions', motions, tiles.motion.detail_row, count=4, #list_item,
                                     sorts={_("oldest"): sorting.entity_oldest,
                                            _("newest"): sorting.entity_newest,
                                            _("activity"): sorting.motion_activity,
                                            _("urgency"): urgency_sort,
                                            _("name"): sorting.delegateable_label},
                                     default_sort=urgency_sort)
        return render("/poll/index.html")
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("poll.create")) 
    def create(self, id):
        self._parse_motion_id(id)
        
        tile = MotionTile(c.motion)
        if not tile.can_begin_poll:
            abort(403, _("The poll cannot be started either because there are "
                       + "no provisions or a poll has already started."))
        
        if request.method == "POST":
            poll = model.Poll(c.motion, c.user)
            model.meta.Session.add(poll)
            model.meta.Session.commit()
            event.emit(event.T_MOTION_STATE_VOTING, {'motion': c.motion},
                       c.user, scopes=[c.instance], topics=[c.motion, c.motion.issue, c.instance])
            redirect_to("/motion/%s" % str(c.motion.id))
        return render("/poll/create.html")
                
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("poll.abort")) 
    def abort(self, id):
        self._parse_motion_id(id)
        auth.require_motion_perm(c.motion, 'poll.abort', enforce_immutability=False)
        if not c.motion.poll:
            h.flash(_("The motion is not undergoing a poll."))
            redirect_to("/motion/%s" % str(c.motion.id))
        
        if request.method == "POST":
            poll = c.motion.poll
            poll.end_time = datetime.now()
            poll.end_user = c.user
            model.meta.Session.add(poll)
            model.meta.Session.commit()
            event.emit(event.T_MOTION_STATE_REDRAFT, {'motion': c.motion},
                       c.user, scopes=[c.instance], topics=[c.motion, c.motion.issue, c.instance])
            redirect_to("/motion/%s" % str(c.motion.id))
            
        return render("/poll/abort.html")                

