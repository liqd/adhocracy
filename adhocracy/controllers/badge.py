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
from adhocracy.lib.instance import RequireInstance

from formencode.schema import SimpleFormValidator
#FIX: Translations
#FIX: HTML/CSS Error message ist wrong
def badgeforminvariant(value_dict, state, validator):
    is_delegateable = value_dict.get('badge_delegateable', "off")
    is_category = value_dict.get('badge_delegateable_category', "off")
    if is_category == is_delegateable == "on":
        return {'state': 'You must not select both "Badge proposal category" and "Badge proposal"'}
BadgeFormInvariant = SimpleFormValidator(badgeforminvariant)

class BadgeForm(formencode.Schema):
    allow_extra_fields = True
    pre_validators = [BadgeFormInvariant,]
    title = All(validators.String(max=40, not_empty=True),
                ContainsChar())
    description = validators.String(max=255)
    color = ValidHTMLColor()
    group = Any(validators.Empty, ValidGroup())
    display_group = validators.StringBoolean(if_missing=False)
    badge_delegateable = validators.StringBoolean(if_missing=False)
    badge_delegateable_category = validators.StringBoolean(if_missing=False)


class BadgeController(BaseController):

    @property
    def base_url(self):
        return h.site.base_url(instance=c.instance, path='/badge')

    @ActionProtector(has_permission("global.admin"))
    def index(self, format='html'):
        #require.user.manage()
        c.badges_users = Badge.all_user(c.instance)
        c.badges_delegateables = Badge.all_delegateable(c.instance)
        c.badges_delegateable_categories = Badge.all_delegateable_categories(c.instance)
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
        badge_delegateable = \
                bool(self.form_result.get('badge_delegateable', ''))
        badge_delegateable_category = \
                bool(self.form_result.get('badge_delegateable_category', ''))
        badge = Badge.create(title, color, description, group, display_group,
                badge_delegateable, badge_delegateable_category, c.instance )
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
                        badge_delegateable_category=badge.badge_delegateable_category,
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

    #TODO: override permission here, the instance admin should do this
    @RequireInstance
    @ActionProtector(has_permission("global.admin"))
    def instance_index(self, format='html'):
        return self.index()

    #TODO: override permission here, the instance admin should do this
    @RequireInstance
    @ActionProtector(has_permission("global.admin"))
    def instance_add(self, errors=None):
        return self.instance_add()

    #TODO: override permission here, the instance admin should do this
    @RequireInternalRequest()
    @RequireInstance
    @validate(schema=BadgeForm(), form='add')
    @ActionProtector(has_permission("global.admin"))
    def instance_create(self):
        return self.create()

    #TODO: override permission here, the instance admin should do this
    @RequireInstance
    @ActionProtector(has_permission("global.admin"))
    def instance_edit(self, id, errors=None):
        return self.edit(id, errors=None)

    #TODO: override permission here, the instance admin should do this
    @RequireInstance
    @RequireInternalRequest()
    @validate(schema=BadgeForm(), form='edit')
    @ActionProtector(has_permission("global.admin"))
    def instance_update(self, id):
        return self.update(id)
