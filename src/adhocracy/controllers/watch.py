import logging

import formencode

from pylons import tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons.decorators import validate
from pylons.i18n import _


from adhocracy import model
import adhocracy.forms as forms
from adhocracy.lib import helpers as h
from adhocracy.lib.auth import require
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib.base import BaseController


log = logging.getLogger(__name__)


class WatchCreateForm(formencode.Schema):
    allow_extra_fields = True
    ref = forms.ValidRef()


class WatchDeleteForm(formencode.Schema):
    allow_extra_fields = True
    watch = forms.ValidWatch()


class WatchController(BaseController):

    @RequireInternalRequest()
    @validate(schema=WatchCreateForm(), form='bad_request', post_only=False,
              on_get=True)
    def create(self, format='html'):
        require.watch.create()
        entity = self.form_result.get('ref')
        if model.Watch.find_by_entity(c.user, entity):
            h.flash(_("A watchlist entry for this entity already exists."),
                    'notice')
        else:
            model.Watch.create(c.user, entity)
            model.meta.Session.commit()
        redirect(h.entity_url(entity))

    @RequireInternalRequest()
    @validate(schema=WatchDeleteForm(), form='bad_request',
              post_only=False, on_get=True)
    def delete(self, format='html'):
        watch = self.form_result.get('watch')
        require.watch.delete(watch)
        if watch.user != c.user and not h.has_permission('instance.admin'):
            abort(403, _("You're not authorized to delete %s's watchlist "
                         "entries.") % watch.user.name)
        watch.delete()
        model.meta.Session.commit()
        redirect(h.entity_url(watch.entity))
