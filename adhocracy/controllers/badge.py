import formencode
from formencode import Any, All, htmlfill, Invalid, validators
from pylons import request, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n import _
from repoze.what.plugins.pylonshq import ActionProtector
from repoze.what.predicates import Any as WhatAnyPredicate

from adhocracy.forms.common import ValidInstanceGroup, ValidHTMLColor, ContainsChar
from adhocracy.forms.common import ValidBadgeInstance
from adhocracy.model import Badge, CategoryBadge, DelegateableBadge, UserBadge,\
    InstanceBadge
from adhocracy.model import Group, Instance, meta
from adhocracy.lib import helpers as h
from adhocracy.lib.auth.authorization import has, has_permission
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render


class BadgeForm(formencode.Schema):
    allow_extra_fields = True
    title = All(validators.String(max=40, not_empty=True),
                ContainsChar())
    description = validators.String(max=255)
    color = ValidHTMLColor()
    instance = ValidBadgeInstance()


class UserBadgeForm(BadgeForm):
    group = Any(validators.Empty, ValidInstanceGroup())
    display_group = validators.StringBoolean(if_missing=False)


AnyAdmin = WhatAnyPredicate(has_permission('global.admin'),
                            has_permission('instance.admin'))


class BadgeController(BaseController):
    """Badge controller base class"""

    form_template = "/badge/form.html"
    index_template = "/badge/index.html"
    base_url_ = None

    def _available_badges(self):
        '''
        Return the badges that are editable by a user.
        '''
        c.groups = [{'permission': 'global.admin',
                     'label': _('In all instances'),
                     'show_label': True}]
        if c.instance:
            c.groups.append(
                {'permission': 'instance.admin',
                 'label': _('In instance "%s"') % c.instance.label,
                 'show_label': h.has_permission('global.admin')})
        badges = {}
        if has('global.admin'):
            badges['global.admin'] = {
                'instance': InstanceBadge.all(instance=None),
                'user': UserBadge.all(instance=None),
                'delegateable': DelegateableBadge.all(instance=None),
                'category': CategoryBadge.all(instance=None)}
        if has('instance.admin') and c.instance is not None:
            badges['instance.admin'] = {
                'instance': InstanceBadge.all(instance=c.instance),
                'user': UserBadge.all(instance=c.instance),
                'delegateable': DelegateableBadge.all(instance=c.instance),
                'category': CategoryBadge.all(instance=c.instance)}
        return badges

    @property
    def base_url(self):
        if self.base_url_ is None:
            self.base_url_ = h.site.base_url(instance=c.instance,
                                             path='/badge')
        return self.base_url_

    def index(self, format='html'):
        c.badges = self._available_badges()
        c.badge_base_url = self.base_url
        return render(self.index_template)

    def _redirect_not_found(self, id):
        h.flash(_("We cannot find the badge with the id %s") % str(id),
                'error')
        redirect(self.base_url)

    def render_form(self):
        q = Instance.all_q().order_by(Instance.label)
        if c.instance:
            q = q.filter(Instance.id != c.instance.id)
        c.other_instances = q.all()
        return render(self.form_template)

    def add(self, badge_type=None, errors=None):
        if badge_type is not None:
            c.badge_type = badge_type
        c.form_type = 'add'
        c.groups = Group.all_instance()
        return htmlfill.render(self.render_form(),
                               defaults=dict(request.params),
                               errors=errors)

    def dispatch(self, action, badge_type, id=None):
        '''
        dispatch to a suiteable "create" or "edit" action

        Methods are named <action>_<badge_type>_badge().
        '''
        assert action in ['create', 'update']
        if badge_type not in ['user', 'delegateable', 'category', 'instance']:
            raise AssertionError('Unknown badge_type: %s' % badge_type)

        c.badge_type = badge_type
        c.form_type = action
        c.badge_base_url = self.base_url

        methodname = "%s_%s_badge" % (action, badge_type)
        method = getattr(self, methodname, None)
        if method is None:
            raise AttributeError(
                'Method not found for action "%s", badge_type: %s' %
                (action, badge_type))
        if id is not None:
            return method(id)
        else:
            return method()

    @ActionProtector(AnyAdmin)
    @RequireInternalRequest()
    def create(self, badge_type):
        return self.dispatch('create', badge_type)

    @ActionProtector(AnyAdmin)
    @RequireInternalRequest()
    def create_instance_badge(self):
        try:
            self.form_result = BadgeForm().to_python(request.params)
        except Invalid, i:
            return self.add('instance', i.unpack_errors())
        title, color, description, instance = self._get_common_fields(
            self.form_result)
        InstanceBadge.create(title, color, description, instance)
        # commit cause redirect() raises an exception
        meta.Session.commit()
        redirect(self.base_url)

    @ActionProtector(AnyAdmin)
    @RequireInternalRequest()
    def create_user_badge(self):
        try:
            self.form_result = UserBadgeForm().to_python(request.params)
        except Invalid, i:
            return self.add('user', i.unpack_errors())

        title, color, description, instance = self._get_common_fields(
            self.form_result)
        group = self.form_result.get('group')
        display_group = self.form_result.get('display_group')
        UserBadge.create(title, color, description, group, display_group,
                         instance)
        # commit cause redirect() raises an exception
        meta.Session.commit()
        redirect(self.base_url)

    @ActionProtector(AnyAdmin)
    @RequireInternalRequest()
    def create_delegateable_badge(self):
        try:
            self.form_result = BadgeForm().to_python(request.params)
        except Invalid, i:
            return self.add('delegateable', i.unpack_errors())
        title, color, description, instance = self._get_common_fields(
            self.form_result)
        DelegateableBadge.create(title, color, description, instance)
        # commit cause redirect() raises an exception
        meta.Session.commit()
        redirect(self.base_url)

    @ActionProtector(AnyAdmin)
    @RequireInternalRequest()
    def create_category_badge(self):
        try:
            self.form_result = BadgeForm().to_python(request.params)
        except Invalid, i:
            return self.add('category', i.unpack_errors())
        title, color, description, instance = self._get_common_fields(
            self.form_result)
        CategoryBadge.create(title, color, description, instance)
        # commit cause redirect() raises an exception
        meta.Session.commit()
        redirect(self.base_url)

    def _get_common_fields(self, form_result):
        '''
        return a tuple of (title, color, description, instance).
        '''
        if h.has_permission('global.admin'):
            instance = form_result.get('instance')
        else:
            # instance only admins can only create/edit
            # badges inside the current instance
            instance = c.instance
        return (form_result.get('title').strip(),
                form_result.get('color').strip(),
                form_result.get('description').strip(),
                instance)

    def get_badge_type(self, badge):
        return badge.polymorphic_identity

    def get_badge_or_redirect(self, id):
        '''
        Get a badge. Redirect if it does not exist. Redirect if it
        if the badge is not from the current instance, but the user is
        only an instance admin, not a global admin
        '''
        badge = Badge.by_id(id, instance_filter=False)
        if badge is None:
            self._redirect_not_found(id)
        if badge.instance != c.instance and not has('global.admin'):
            self._redirect_not_found(id)
        return badge

    @ActionProtector(AnyAdmin)
    def edit(self, id, errors=None):
        badge = self.get_badge_or_redirect(id)
        c.badge_type = self.get_badge_type(badge)
        c.form_type = 'update'

        # form defaults
        instance_default = badge.instance.key if badge.instance else ''
        defaults = dict(title=badge.title,
                        description=badge.description,
                        color=badge.color,
                        display_group=badge.display_group,
                        instance=instance_default)
        if isinstance(badge, UserBadge):
            c.groups = Group.all_instance()
            defaults['group'] = badge.group and badge.group.code or ''

        return htmlfill.render(self.render_form(),
                               errors=errors,
                               defaults=defaults)

    @ActionProtector(AnyAdmin)
    @RequireInternalRequest()
    def update(self, id):
        badge = self.get_badge_or_redirect(id)
        c.badge_type = self.get_badge_type(badge)
        return self.dispatch('update', c.badge_type, id=id)

    @ActionProtector(AnyAdmin)
    @RequireInternalRequest()
    def update_user_badge(self, id):
        try:
            self.form_result = UserBadgeForm().to_python(request.params)
        except Invalid, i:
            return self.edit(id, i.unpack_errors())

        badge = self.get_badge_or_redirect(id)
        title, color, description, instance = self._get_common_fields(
            self.form_result)
        group = self.form_result.get('group')
        display_group = self.form_result.get('display_group')

        badge.group = group
        badge.title = title
        badge.color = color
        badge.description = description
        badge.instance = instance
        badge.display_group = display_group
        meta.Session.commit()
        h.flash(_("Badge changed successfully"), 'success')
        redirect(self.base_url)

    @ActionProtector(AnyAdmin)
    @RequireInternalRequest()
    def update_delegateable_badge(self, id):
        try:
            self.form_result = BadgeForm().to_python(request.params)
        except Invalid, i:
            return self.edit(id, i.unpack_errors())
        badge = self.get_badge_or_redirect(id)
        title, color, description, instance = self._get_common_fields(
            self.form_result)

        badge.title = title
        badge.color = color
        badge.description = description
        badge.instance = instance
        meta.Session.commit()
        h.flash(_("Badge changed successfully"), 'success')
        redirect(self.base_url)

    @ActionProtector(AnyAdmin)
    @RequireInternalRequest()
    def update_instance_badge(self, id):
        try:
            self.form_result = BadgeForm().to_python(request.params)
        except Invalid, i:
            return self.edit(id, i.unpack_errors())
        badge = self.get_badge_or_redirect(id)
        title, color, description, instance = self._get_common_fields(
            self.form_result)

        badge.title = title
        badge.color = color
        badge.description = description
        badge.instance = instance
        meta.Session.commit()
        h.flash(_("Badge changed successfully"), 'success')
        redirect(self.base_url)

    @ActionProtector(AnyAdmin)
    @RequireInternalRequest()
    def update_category_badge(self, id):
        try:
            self.form_result = BadgeForm().to_python(request.params)
        except Invalid, i:
            return self.edit(id, i.unpack_errors())
        badge = self.get_badge_or_redirect(id)
        title, color, description, instance = self._get_common_fields(
            self.form_result)

        badge.title = title
        badge.color = color
        badge.description = description
        badge.instance = instance
        meta.Session.commit()
        h.flash(_("Badge changed successfully"), 'success')
        redirect(self.base_url)
