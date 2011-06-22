from operator import attrgetter

import formencode
from formencode import htmlfill, validators
from pylons import request, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.decorators import validate
from pylons.i18n import _


from adhocracy.forms.common import ValidHTMLColor
from adhocracy.model import Badge, meta
from adhocracy.lib import helpers as h
from adhocracy.lib.auth import require
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render, render_json


class BadgeForm(formencode.Schema):
    allow_extra_fields = True
    title = validators.String(max=40, not_empty=True)
    color = ValidHTMLColor()


class BadgeController(BaseController):

    base_url = h.site.base_url(instance=None, path='/badge')

    def index(self, format='html'):
        #require.user.manage()
        badges = Badge.all()
        if format == 'json':
            return render_json([badge.to_dict() for badge in badges])
        c.badges = sorted(badges, key=attrgetter('title'))
        return render("/badge/index.html")

    def _redirect_not_found(self, id):
        h.flash(_("We cannot find the badge with the id %s") % str(id),
                'error')
        redirect(self.base_url)

    def add(self, errors=None):
        c.form_title = c.save_button = _("Add Badge")
        c.action_url = self.base_url + '/add'
        return htmlfill.render(render("/badge/form.html"),
                               defaults=dict(request.params),
                               errors=errors)

    @RequireInternalRequest()
    @validate(schema=BadgeForm(), form='add')
    def create(self):
        title = self.form_result.get('title').strip()
        color = self.form_result.get('color').strip()
        badge = Badge.create(title, color)
        meta.Session.add(badge)
        meta.Session.commit()
        redirect(self.base_url)

    def edit(self, id, errors=None):
        c.form_title = c.save_button = _("Edit Badge")
        c.action_url = self.base_url + '/edit/%s' % id
        badge = Badge.by_id(id)
        if badge is None:
            self._redirect_not_found(id)
        defaults = dict(title=badge.title,
                        color=badge.color)
        return htmlfill.render(render("/badge/form.html"),
                               errors=errors,
                               defaults=defaults)

    @RequireInternalRequest()
    @validate(schema=BadgeForm(), form='edit')
    def update(self, id):
        require.user.manage(c.user)
        badge = Badge.by_id(id)
        if badge is None:
            self._redirect_not_found(id)

        title = self.form_result.get('title').strip()
        color = self.form_result.get('color').strip()
        badge.title = title
        badge.color = color
        meta.Session.commit()
        h.flash(_("Badge changed successfully"))
        redirect(self.base_url)
