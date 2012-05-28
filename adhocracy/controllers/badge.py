import formencode
from formencode import Any, All, htmlfill, validators
from pylons import request, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.decorators import validate
from pylons.i18n import _
from repoze.what.plugins.pylonshq import ActionProtector
from repoze.what.predicates import Any as WhatAnyPredicate

from adhocracy.forms.common import ValidGroup, ValidHTMLColor, ContainsChar
from adhocracy.forms.common import ValidBadgeInstance
from adhocracy.model import Badge, CategoryBadge, DelegateableBadge, UserBadge
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
    group = Any(validators.Empty, ValidGroup())
    display_group = validators.StringBoolean(if_missing=False)


AnyAdmin = WhatAnyPredicate(has_permission('global.admin'),
                            has_permission('instance.admin'))


class BadgeController(BaseController):
    """Badge controller base class"""

    def _available_badges(self):
        '''
        Return the badges that are editable by a user.
        '''
        c.groups = [{'permission': 'global.admin',
                     'label': _('In all instances')}]
        if c.instance:
            c.groups.append(
                {'permission': 'instance.admin',
                 'label': _('In instance "%s"') % c.instance.label})
        badges = {}
        if has('global.admin'):
            badges['global.admin'] = {
                'user': UserBadge.all(instance=None),
                'delegateable': DelegateableBadge.all(instance=None),
                'category': CategoryBadge.all(instance=None)}
        if has('instance.admin') and c.instance is not None:
            badges['instance.admin'] = {
                'user': UserBadge.all(instance=c.instance),
                'delegateable': DelegateableBadge.all(instance=c.instance),
                'category': CategoryBadge.all(instance=c.instance)}
        return badges

    @property
    def base_url(self):
        return h.site.base_url(instance=c.instance, path='/badge')

    def index(self, format='html'):
        c.badges = self._available_badges()
        return render("/badge/index.html")

    def _redirect_not_found(self, id):
        h.flash(_("We cannot find the badge with the id %s") % str(id),
                'error')
        redirect(self.base_url)

    def render_form(self):
        c.instances = Instance.all()
        return render("/badge/form.html")

    def add(self, badge_type=None, errors=None):
        if badge_type is not None:
            c.badge_type = badge_type
        c.form_type = 'add'
        c.groups = meta.Session.query(Group).order_by(Group.group_name).all()
        return htmlfill.render(self.render_form(),
                               defaults=dict(request.params),
                               errors=errors)

    def dispatch(self, action, badge_type, id=None):
        '''
        dispatch to a suiteable "create" or "edit" action

        Methods are named <action>_<badge_type>_badge().
        '''
        assert action in ['create', 'update']
        if badge_type not in ['user', 'delegateable', 'category']:
            raise AssertionError('Unknown badge_type: %s' % badge_type)

        c.badge_type = badge_type
        c.form_type = action

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
    @validate(schema=UserBadgeForm(), form='add')
    def create_user_badge(self):
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
    @validate(schema=BadgeForm(), form='add')
    def create_delegateable_badge(self):
        title, color, description, instance = self._get_common_fields(
            self.form_result)
        DelegateableBadge.create(title, color, description, instance)
        # commit cause redirect() raises an exception
        meta.Session.commit()
        redirect(self.base_url)

    @ActionProtector(AnyAdmin)
    @RequireInternalRequest()
    @validate(schema=BadgeForm(), form='add')
    def create_category_badge(self):
        title, color, description, instance = self._get_common_fields(
            self.form_result)
        CategoryBadge.create(title, color, description, instance)
        # commit cause redirect() raises an exception
        meta.Session.commit()
        redirect(self.base_url)

    def _get_common_fields(self, form_result):
        return (form_result.get('title').strip(),
                form_result.get('color').strip(),
                form_result.get('description').strip(),
                form_result.get('instance'))

    def get_badge_type(self, badge):
        return badge.polymorphic_identity

    @ActionProtector(AnyAdmin)
    def edit(self, id, errors=None):
        badge = Badge.by_id(id, instance_filter=False)
        if badge is None:
            self._redirect_not_found(id)
        if badge.instance != c.instance and not has('global.admin'):
            self._redirect_not_found(id)
        c.badge_type = self.get_badge_type(badge)
        c.form_type = 'update'
        instance_default = badge.instance.key if badge.instance else ''
        defaults = dict(title=badge.title,
                        description=badge.description,
                        color=badge.color,
                        display_group=badge.display_group,
                        instance=instance_default)
        if isinstance(badge, UserBadge):
            c.groups = meta.Session.query(Group).order_by(Group.group_name)
            defaults['group'] = badge.group and badge.group.code or ''
        return htmlfill.render(self.render_form(),
                               errors=errors,
                               defaults=defaults)

    @ActionProtector(AnyAdmin)
    @RequireInternalRequest()
    def update(self, id):
        badge = Badge.by_id(id, instance_filter=False)
        if badge is None:
            self._redirect_not_found(id)
        if badge.instance != c.instance and not has('global.admin'):
            self._redirect_not_found(id)
        c.badge_type = self.get_badge_type(badge)
        return self.dispatch('update', c.badge_type, id=id)

    @ActionProtector(AnyAdmin)
    @RequireInternalRequest()
    @validate(schema=UserBadgeForm(), form='edit')
    def update_user_badge(self, id):
        badge = Badge.by_id(id)
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
    @validate(schema=BadgeForm(), form='edit')
    def update_delegateable_badge(self, id):
        badge = Badge.by_id(id)
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
    @validate(schema=BadgeForm(), form='edit')
    def update_category_badge(self, id):
        badge = Badge.by_id(id)
        title, color, description, instance = self._get_common_fields(
            self.form_result)

        badge.title = title
        badge.color = color
        badge.description = description
        badge.instance = instance
        meta.Session.commit()
        h.flash(_("Badge changed successfully"), 'success')
        redirect(self.base_url)
