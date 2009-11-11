import logging
from datetime import datetime

from adhocracy.lib.base import *
from adhocracy.lib.tiles.motion_tiles import MotionTile

log = logging.getLogger(__name__)

class PollController(BaseController):

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

