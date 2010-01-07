import logging
from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.model.refs as refs
import adhocracy.model.forms as forms

log = logging.getLogger(__name__)

class WatchCreateForm(formencode.Schema):
    allow_extra_fields = True
    ref = validators.String(not_empty=True)
    ret = validators.String(not_empty=False, if_empty='/', if_missing='/')

class WatchDeleteForm(formencode.Schema):
    allow_extra_fields = True
    watch = forms.ValidWatch()
    ret = validators.String(not_empty=False, if_empty='/', if_missing='/')

WATCH_PERMISSIONS = {'comment': 'comment.view',
                     'proposal': 'proposal.view',
                     'issue': 'issue.view',
                     'category': 'category.view',
                     'instance': 'instance.view',
                     'user': 'user.view'}

class WatchController(BaseController):
        
    @RequireInstance
    @RequireInternalRequest()
    @validate(schema=WatchCreateForm(), post_only=False, on_get=True)
    def create(self, format='html'):
        if not hasattr(self, 'form_result'):
            h.flash(_("Invalid request."))
            redirect_to('/')
        ref = self.form_result.get('ref')
        ref_type = refs.ref_type(ref)
        if not ref_type or (not ref_type in WATCH_PERMISSIONS.keys()):
            abort(404, _("Invalid entity reference in watchlist request."))
        if not h.has_permission(WATCH_PERMISSIONS[ref_type]):
            abort(403, _("No permission to create watches on a %s") % ref_type)
        if watchlist.get_ref_watch(c.user, ref):
            abort(500, _("A watchlist entry for this entity already exists."))
        watchlist.watch_ref(c.user, ref)    
        if format == 'json':
            return "OK"
        redirect_to(str(self.form_result.get('ret')))
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("watch.delete"))
    @validate(schema=WatchDeleteForm(), post_only=False, on_get=True)
    def delete(self, format='html'):
        if not hasattr(self, 'form_result'):
            h.flash(_("Invalid request."))
            redirect_to('/')
        watch = self.form_result.get('watch')
        if watch.user != c.user and not \
            (h.has_permission('instance.admin') or \
             h.has_permission('global.admin')):
            abort(403, _("You're not authorized to delete %s's watchlist entries.") % watch.user.name)
        watch.delete_time = datetime.now()
        model.meta.Session.add(watch)
        model.meta.Session.commit()
        if format == 'json':
            return "OK"
        redirect_to(str(self.form_result.get('ret')))
        
