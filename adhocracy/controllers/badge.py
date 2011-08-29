from operator import attrgetter

import formencode
from formencode import Any, All, htmlfill, validators
from pylons import request, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.decorators import validate
from pylons.i18n import _
from repoze.what.plugins.pylonshq import ActionProtector

from adhocracy.forms.common import ValidGroup, ValidHTMLColor, ContainsChar
from adhocracy.model import Badge, Group, meta
from adhocracy.lib import helpers as h
from adhocracy.lib.auth.authorization import has_permission
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render, render_json


class BadgeForm(formencode.Schema):
    allow_extra_fields = True
    title = All(validators.String(max=40, not_empty=True),
                ContainsChar())
    description = validators.String(max=255)
    color = ValidHTMLColor()
    group = Any(validators.Empty, ValidGroup())
    display_group = validators.StringBoolean(if_missing=False)
    badge_delegateable = validators.StringBoolean(if_missing=False)


class BadgeController(BaseController):

    base_url = h.site.base_url(instance=None, path='/badge')

    @ActionProtector(has_permission("global.admin"))
    def index(self, format='html'):
        #require.user.manage()
        badges = Badge.all()
        if format == 'json':
            return render_json([badge.to_dict() for badge in badges])
        badges_users = filter(lambda x: not x.badge_delegateable, badges)
        c.badges_users = sorted(badges_users, key=attrgetter('title'))
        badges_delegateables = filter(lambda x: x.badge_delegateable, badges)
        c.badges_delegateables = sorted(badges_delegateables, key=attrgetter('title'))
        return render("/badge/index.html")

    def _redirect_not_found(self, id):
        h.flash(_("We cannot find the badge with the id %s") % str(id),
                'error')
        redirect(self.base_url)

    @ActionProtector(has_permission("global.admin"))
    def add(self, errors=None):
        c.form_title = c.save_button = _("Add Badge")
        c.action_url = self.base_url + '/add'
        c.groups = meta.Session.query(Group).order_by(Group.group_name).all()
        return htmlfill.render(render("/badge/form.html"),
                               defaults=dict(request.params),
                               errors=errors)

    @RequireInternalRequest()
    @validate(schema=BadgeForm(), form='add')
    @ActionProtector(has_permission("global.admin"))
    def create(self):
        title = self.form_result.get('title').strip()
        description = self.form_result.get('description').strip()
        color = self.form_result.get('color').strip()
        group = self.form_result.get('group')
        display_group = self.form_result.get('display_group')
        badge_delegateable = bool(self.form_result.get('badge_delegateable'))
        badge = Badge.create(title, color, description, group, display_group, badge_delegateable)
        meta.Session.add(badge)
        meta.Session.commit()
        redirect(self.base_url)

    @ActionProtector(has_permission("global.admin"))
    def edit(self, id, errors=None):
        c.form_title = c.save_button = _("Edit Badge")
        c.action_url = self.base_url + '/edit/%s' % id
        c.groups = meta.Session.query(Group).order_by(Group.group_name).all()
        badge = Badge.by_id(id)
        if badge is None:
            self._redirect_not_found(id)
        group_default = badge.group and badge.group.code or ''
        defaults = dict(title=badge.title,
                        description=badge.description,
                        color=badge.color,
                        group=group_default,
                        display_group=badge.display_group,
                        badge_delegateable=badge.badge_delegateable, 
                        )
        
        return htmlfill.render(render("/badge/form.html"),
                               errors=errors,
                               defaults=defaults)

    @RequireInternalRequest()
    @validate(schema=BadgeForm(), form='edit')
    @ActionProtector(has_permission("global.admin"))
    def update(self, id):
        badge = Badge.by_id(id)
        if badge is None:
            self._redirect_not_found(id)

        title = self.form_result.get('title').strip()
        description = self.form_result.get('description').strip()
        color = self.form_result.get('color').strip()
        group = self.form_result.get('group')
        display_group = self.form_result.get('display_group')

        if group:
            badge.group = group
        else:
            badge.group = None
        badge.title = title
        badge.color = color
        badge.description = description
        badge.display_group = display_group
        meta.Session.commit()
        h.flash(_("Badge changed successfully"), 'success')
        redirect(self.base_url)
