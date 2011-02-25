import logging
from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.model.refs as refs
import adhocracy.forms as forms

log = logging.getLogger(__name__)

class WatchCreateForm(formencode.Schema):
    allow_extra_fields = True
    ref = forms.ValidRef()

class WatchDeleteForm(formencode.Schema):
    allow_extra_fields = True
    watch = forms.ValidWatch()

class WatchController(BaseController):
    
    @RequireInternalRequest()
    @validate(schema=WatchCreateForm(), form='bad_request', post_only=False, on_get=True)
    def create(self, format='html'):
        require.watch.create()
        entity = self.form_result.get('ref')
        if model.Watch.find_by_entity(c.user, entity):
            h.flash(_("A watchlist entry for this entity already exists."),
                    'notice')
        else:
            watch = model.Watch.create(c.user, entity)
            model.meta.Session.commit()
        redirect(h.entity_url(entity))
    
    
    @RequireInternalRequest()
    @validate(schema=WatchDeleteForm(), form='bad_request', post_only=False, on_get=True)
    def delete(self, format='html'):
        watch = self.form_result.get('watch')
        require.watch.delete(watch)
        if watch.user != c.user and not h.has_permission('instance.admin'):
            abort(403, _("You're not authorized to delete %s's watchlist entries.") % watch.user.name)
        watch.delete()
        model.meta.Session.commit()
        redirect(h.entity_url(watch.entity))
