import logging

from cgi import FieldStorage
import formencode
from formencode import Any, All, htmlfill, Invalid, validators
from paste.deploy.converters import asbool
from pylons import request, tmpl_context as c
from pylons.controllers.util import abort
from pylons.controllers.util import redirect
from pylons.i18n import _

from adhocracy import config
from adhocracy.forms.common import ValidInstanceGroup
from adhocracy.forms.common import ValidHTMLColor
from adhocracy.forms.common import ContainsChar
from adhocracy.forms.common import ValidBadgeInstance
from adhocracy.forms.common import ValidImageFileUpload
from adhocracy.forms.common import ValidFileUpload
from adhocracy.forms.common import ValidCategoryBadge
from adhocracy.forms.common import ValidParentCategory
from adhocracy.forms.common import ValidateNoCycle
from adhocracy.forms.common import ProposalSortOrder
from adhocracy.model import UPDATE
from adhocracy.model import meta
from adhocracy.model import Badge
from adhocracy.model import Group
from adhocracy.model import CategoryBadge
from adhocracy.model import DelegateableBadge
from adhocracy.model import InstanceBadge
from adhocracy.model import ThumbnailBadge
from adhocracy.model import UserBadge
from adhocracy.lib import helpers as h, logo
from adhocracy.lib.auth.authorization import has
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib.auth import require
from adhocracy.lib.auth import guard
from adhocracy.lib.auth import can
from adhocracy.lib.base import BaseController
from adhocracy.lib.behavior import behavior_enabled
from adhocracy.lib.pager import PROPOSAL_SORTS
from adhocracy.lib.queue import update_entity
from adhocracy.lib.templating import render
from adhocracy.lib.templating import OVERLAY_SMALL


log = logging.getLogger(__name__)


BADGE_TYPE_MAPPING = {
    'user': UserBadge,
    'delegateable': DelegateableBadge,
    'category': CategoryBadge,
    'instance': InstanceBadge,
    'thumbnail': ThumbnailBadge,
}


class BadgeForm(formencode.Schema):
    allow_extra_fields = True
    title = All(validators.String(max=40, not_empty=True),
                ContainsChar())
    description = validators.String(max=255)
    color = ValidHTMLColor()
    instance = ValidBadgeInstance()
    impact = validators.Int(min=-10, max=10, if_missing=0)
    if behavior_enabled():
        behavior_proposal_sort_order = ProposalSortOrder()


class CategoryBadgeForm(BadgeForm):
    select_child_description = validators.String(max=255)
    parent = ValidCategoryBadge(not_empty=False)
    long_description = validators.String(
        max=config.get_int('adhocracy.category.long_description.max_length'))
    chained_validators = [
        # make sure parent has same instance as we
        ValidParentCategory()
    ]


class CategoryBadgeUpdateForm(CategoryBadgeForm):
    id = ValidCategoryBadge(not_empty=True)
    chained_validators = [
        # make sure parent has same instance as we
        ValidParentCategory(),
        # make sure we don't create a cycle
        ValidateNoCycle(),
    ]


class UserBadgeForm(BadgeForm):
    pass


class UserBadgeFormSupervise(UserBadgeForm):
    group = Any(validators.Empty, ValidInstanceGroup())
    display_group = validators.StringBoolean(if_missing=False)


class ThumbnailBadgeForm(BadgeForm):
    thumbnail = All(ValidImageFileUpload(not_empty=False),
                    ValidFileUpload(not_empty=False), )


class BadgeController(BaseController):
    """Badge controller base class"""

    form_template = "/badge/form.html"
    index_template = "/badge/index.html"
    base_url_ = None
    identifier = "badges"

    @property
    def base_url(self):
        if self.base_url_ is None:
            self.base_url_ = h.site.base_url(instance=c.instance,
                                             path='/badge')
        return self.base_url_

    def _get_badge_data(self, badge_type):
        cls = self._get_badge_class(badge_type)
        if cls is None:
            abort(404, _(u"No such badge type"))

        return {
            'badge_type': badge_type,
            'badge_header': self._get_badge_header(badge_type),
            'badge_base_url': self.base_url,
            'global_badges': (cls.all(instance=None)
                              if has('global.admin')
                              else None),
            'instance_badges': (cls.all(instance=c.instance)
                                if c.instance is not None
                                else None),
        }

    def _redirect(self):
        if c.came_from:
            redirect(c.came_from)
        else:
            redirect(self.base_url)

    @guard.perm('badge.index')
    def index(self, format='html'):
        c.badge_tables = dict((type_, self._get_badge_data(type_))
                              for type_ in ['user', 'category', 'thumbnail',
                                            'delegateable', 'instance'])
        return render('/badge/index_all.html', overlay=format == u'overlay')

    @guard.perm('badge.index')
    def index_type(self, badge_type, format='html'):
        data = self._get_badge_data(badge_type)
        data['came_from'] = self.base_url + '/' + badge_type
        return render(self.index_template, data, overlay=format == u'overlay',
                      overlay_size=OVERLAY_SMALL)

    def _redirect_not_found(self, id):
        h.flash(_("We cannot find the badge with the id %s") % str(id),
                'error')
        self._redirect()

    def _set_parent_categories(self, exclude=None):
        local_categories = CategoryBadge.all_q(instance=c.instance)

        if exclude is not None:
            local_categories = filter(lambda c: not(c.is_ancester(exclude)),
                                      local_categories)

        c.local_category_parents = sorted(
            [(b.id, b.get_key()) for b in local_categories],
            key=lambda x: x[1])

        if h.has_permission('global.admin'):
            global_categories = CategoryBadge.all_q(instance=None)

            if exclude is not None:
                global_categories = filter(
                    lambda c: not(c.is_ancester(exclude)), global_categories)
            c.global_category_parents = sorted(
                [(b.id, b.get_key()) for b in global_categories],
                key=lambda x: x[1])

    def add(self, badge_type=None, errors=None, format=u'html'):
        data = {
            'form_type': 'add',
            'groups': Group.all_instance(),
            'sorting_orders': PROPOSAL_SORTS,
        }
        if not c.came_from:
            c.came_from = self.base_url
        if badge_type is not None:
            data['badge_type'] = badge_type

        if (c.instance is not None
           and not asbool(request.GET.get('global', False))):
            require.badge.manage_instance()
            instance = c.instance.key
        else:
            require.badge.manage_global()
            instance = ''

        defaults = {'visible': True,
                    'select_child_description': '',
                    'impact': 0,
                    'instance': instance,
                    }
        defaults.update(dict(request.params))

        self._set_parent_categories()

        html = render(self.form_template, data, overlay=format == u'overlay',
                      overlay_size=OVERLAY_SMALL)
        return htmlfill.render(html,
                               defaults=defaults,
                               errors=errors,
                               force_defaults=False)

    def _dispatch(self, action, badge_type, id=None, format=u'html'):
        '''
        dispatch to a suitable "create" or "edit" action

        Methods are named <action>_<badge_type>_badge().
        '''
        assert action in ['create', 'update']
        types = ['user', 'delegateable', 'category', 'instance', 'thumbnail']
        if badge_type not in types:
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
            return method(id, format=format)
        else:
            return method(format=format)

    @RequireInternalRequest()
    def create(self, badge_type, format=u'html'):
        return self._dispatch('create', badge_type, format=format)

    @RequireInternalRequest()
    def create_instance_badge(self, format=u'html'):
        try:
            self.form_result = BadgeForm().to_python(request.params)
        except Invalid as i:
            return self.add('instance', i.unpack_errors(), format=format)
        title, color, visible, description, impact, instance =\
            self._get_common_fields(self.form_result)

        if instance is None:
            require.badge.manage_global()
        else:
            require.badge.manage_instance()

        InstanceBadge.create(title, color, visible, description, impact,
                             instance)
        # commit cause redirect() raises an exception
        meta.Session.commit()
        self._redirect()

    @RequireInternalRequest()
    def create_user_badge(self, format=u'html'):
        try:
            if can.user.supervise():
                form = UserBadgeFormSupervise()
            else:
                form = UserBadgeForm()
            self.form_result = form.to_python(request.params)
        except Invalid as i:
            return self.add('user', i.unpack_errors(), format=format)

        title, color, visible, description, impact, instance =\
            self._get_common_fields(self.form_result)

        if instance is None:
            require.badge.manage_global()
        else:
            require.badge.manage_instance()

        if can.user.supervise():
            group = self.form_result.get('group')
            display_group = self.form_result.get('display_group')

            UserBadge.create(title, color, visible, description,
                             group=group,
                             display_group=display_group,
                             impact=impact,
                             instance=instance)
        else:
            UserBadge.create(title, color, visible, description,
                             impact=impact,
                             instance=instance)

        # commit cause redirect() raises an exception
        meta.Session.commit()
        self._redirect()

    @RequireInternalRequest()
    def create_delegateable_badge(self, format=u'html'):
        try:
            self.form_result = BadgeForm().to_python(request.params)
        except Invalid as i:
            return self.add('delegateable', i.unpack_errors(), format=format)
        title, color, visible, description, impact, instance =\
            self._get_common_fields(self.form_result)

        if instance is None:
            require.badge.manage_global()
        else:
            require.badge.manage_instance()

        DelegateableBadge.create(title, color, visible, description, impact,
                                 instance)
        # commit cause redirect() raises an exception
        meta.Session.commit()
        self._redirect()

    @RequireInternalRequest()
    def create_category_badge(self, format=u'html'):
        try:
            self.form_result = CategoryBadgeForm().to_python(request.params)
        except Invalid as i:
            return self.add('category', i.unpack_errors(), format=format)

        title, color, visible, description, impact, instance =\
            self._get_common_fields(self.form_result)

        if instance is None:
            require.badge.manage_global()
        else:
            require.badge.manage_instance()

        child_descr = self.form_result.get("select_child_description")
        child_descr = child_descr.replace("$badge_title", title)
        long_description = self.form_result.get("long_description")
        parent = self.form_result.get("parent")
        parent = self.form_result.get("parent")
        if parent and parent.id == id:
            parent = None
        badge = CategoryBadge.create(title, color, visible, description,
                                     impact, instance, parent=parent,
                                     long_description=long_description,
                                     select_child_description=child_descr)

        try:
            # fixme: show image errors in the form
            if ('image' in request.POST and
                    hasattr(request.POST.get('image'), 'file') and
                    request.POST.get('image').file):
                logo.store(badge, request.POST.get('image').file)
        except Exception, e:
            meta.Session.rollback()
            h.flash(unicode(e), 'error')
            log.debug(e)
            return self.add('category', format=format)

        # commit cause redirect() raises an exception
        meta.Session.commit()
        self._redirect()

    @RequireInternalRequest()
    def create_thumbnail_badge(self, format=u'html'):
        try:
            self.form_result = BadgeForm().to_python(request.params)
        except Invalid as i:
            return self.add('thumbnail', i.unpack_errors(), format=format)
        title, color, visible, description, impact, instance =\
            self._get_common_fields(self.form_result)

        if instance is None:
            require.badge.manage_global()
        else:
            require.badge.manage_instance()

        thumbnail = self.form_result.get("thumbnail")
        if isinstance(thumbnail, FieldStorage):
            thumbnail = thumbnail.file.read()
        else:
            thumbnail = None
        ThumbnailBadge.create(title, color, visible, description, thumbnail,
                              impact, instance)
        # commit cause redirect() raises an exception
        meta.Session.commit()
        self._redirect()

    def _get_common_fields(self, form_result):
        '''
        return a tuple of (title, color, visible, description, impact,
                           instance).
        '''
        if h.has_permission('global.admin'):
            instance = form_result.get('instance')
        else:
            # instance only admins can only create/edit
            # badges inside the current instance
            instance = c.instance
        return (form_result.get('title').strip(),
                form_result.get('color').strip(),
                'visible' in form_result,
                form_result.get('description').strip(),
                form_result.get('impact'),
                instance,
                )

    def _get_badge_type(self, badge):
        return badge.polymorphic_identity

    def _get_badge_class(self, badge_type):
        return BADGE_TYPE_MAPPING.get(badge_type)

    def _get_badge_header(self, badge_type):
        BADGE_HEADERS = {
            'user': _(u'User Badges'),
            'delegateable': _(u'Proposal Badges'),
            'category': _(u'Categories'),
            'instance': _(u'Instance Badges'),
            'thumbnail': _(u'Status Badges'),
        }
        return BADGE_HEADERS.get(badge_type)

    def _get_badge_or_redirect(self, id):
        '''
        Get a badge. Redirect if it does not exist. Redirect if
        the badge is not from the current instance, but the user is
        only an instance admin, not a global admin
        '''
        badge = Badge.by_id(id, instance_filter=False)
        if badge is None:
            self._redirect_not_found(id)
        if badge.instance != c.instance and not has('global.admin'):
            self._redirect_not_found(id)
        return badge

    def edit(self, id, errors=None, format=u'html'):
        badge = self._get_badge_or_redirect(id)
        require.badge.edit(badge)

        if not c.came_from:
            # if badge has entity_url, redirect there
            try:
                c.came_from = h.entity_url(badge)
            except ValueError:
                pass

        data = {
            'badge_type': self._get_badge_type(badge),
            'form_type': 'update',
            'return_url': self.base_url,
            'sorting_orders': PROPOSAL_SORTS,
        }
        if getattr(badge, "thumbnail", None):
            data['logo'] = h.badge_helper.generate_thumbnail_tag(badge)
        elif self._get_badge_type(badge) == 'category' and logo.exists(badge):
            data['logo'] = '<img src="%s" />' % h.logo_url(badge, 48)

        self._set_parent_categories(exclude=badge)

        # Plug in current values
        instance_default = badge.instance.key if badge.instance else ''
        defaults = dict(
            title=badge.title,
            description=badge.description,
            long_description=badge.long_description,
            color=badge.color,
            visible=badge.visible,
            display_group=badge.display_group,
            impact=badge.impact,
            instance=instance_default,
            behavior_proposal_sort_order=badge.behavior_proposal_sort_order)
        if isinstance(badge, UserBadge):
            c.groups = Group.all_instance()
            defaults['group'] = badge.group and badge.group.code or ''
        if isinstance(badge, CategoryBadge):
            defaults['parent'] = badge.parent and badge.parent.id or ''
            defaults['select_child_description'] =\
                badge.select_child_description

        if not c.came_from:
            c.came_from = self.base_url

        return htmlfill.render(render(self.form_template, data,
                                      overlay=format == u'overlay',
                                      overlay_size=OVERLAY_SMALL),
                               errors=errors,
                               defaults=defaults,
                               force_defaults=False)

    @RequireInternalRequest()
    def update(self, id, format=u'html'):
        badge = self._get_badge_or_redirect(id)
        require.badge.edit(badge)
        c.badge_type = self._get_badge_type(badge)
        return self._dispatch('update', c.badge_type, id=id, format=format)

    @RequireInternalRequest()
    def update_user_badge(self, id, format=u'html'):
        try:
            if can.user.supervise():
                form = UserBadgeFormSupervise()
            else:
                form = UserBadgeForm()
            self.form_result = form.to_python(request.params)
        except Invalid as i:
            return self.edit(id, i.unpack_errors(), format=format)

        badge = self._get_badge_or_redirect(id)
        require.badge.edit(badge)
        title, color, visible, description, impact, instance =\
            self._get_common_fields(self.form_result)

        badge.title = title
        badge.color = color
        badge.visible = visible
        badge.description = description
        badge.instance = instance
        if can.user.supervise():
            badge.group = self.form_result.get('group')
            badge.display_group = self.form_result.get('display_group')
        if behavior_enabled():
            badge.behavior_proposal_sort_order = self.form_result.get(
                'behavior_proposal_sort_order')
        if badge.impact != impact:
            badge.impact = impact
            meta.Session.commit()
            for user in badge.users:
                update_entity(user, UPDATE)
        else:
            meta.Session.commit()
        h.flash(_("Badge changed successfully"), 'success')
        self._redirect()

    @RequireInternalRequest()
    def update_delegateable_badge(self, id, format=u'html'):
        try:
            self.form_result = BadgeForm().to_python(request.params)
        except Invalid as i:
            return self.edit(id, i.unpack_errors(), format=format)
        badge = self._get_badge_or_redirect(id)
        require.badge.edit(badge)
        title, color, visible, description, impact, instance =\
            self._get_common_fields(self.form_result)

        badge.title = title
        badge.color = color
        badge.visible = visible
        badge.description = description
        badge.instance = instance
        if badge.impact != impact:
            badge.impact = impact
            meta.Session.commit()
            for delegateable in badge.delegateables:
                update_entity(delegateable, UPDATE)
        else:
            meta.Session.commit()
        h.flash(_("Badge changed successfully"), 'success')
        self._redirect()

    @RequireInternalRequest()
    def update_instance_badge(self, id, format=u'html'):
        try:
            self.form_result = BadgeForm().to_python(request.params)
        except Invalid as i:
            return self.edit(id, i.unpack_errors(), format=format)
        badge = self._get_badge_or_redirect(id)
        require.badge.edit(badge)
        title, color, visible, description, impact, instance =\
            self._get_common_fields(self.form_result)

        badge.title = title
        badge.color = color
        badge.visible = visible
        badge.description = description
        badge.instance = instance
        if badge.impact != impact:
            badge.impact = impact
            meta.Session.commit()
            for instance in badge.instances:
                update_entity(instance, UPDATE)
        else:
            meta.Session.commit()
        h.flash(_("Badge changed successfully"), 'success')
        self._redirect()

    @RequireInternalRequest()
    def update_category_badge(self, id, format=u'html'):
        try:
            params = request.params.copy()
            params['id'] = id
            self.form_result = CategoryBadgeUpdateForm().to_python(params)
        except Invalid as i:
            return self.edit(id, i.unpack_errors(), format=format)
        badge = self._get_badge_or_redirect(id)
        require.badge.edit(badge)

        # delete the logo if the button was pressed and exit
        if 'delete_image' in self.form_result:
            updated = logo.delete(badge)
            if updated:
                h.flash(_(u'The image has been deleted.'), 'success')
            self._redirect()

        try:
            # fixme: show image errors in the form
            if ('image' in request.POST and
                    hasattr(request.POST.get('image'), 'file') and
                    request.POST.get('image').file):
                logo.store(badge, request.POST.get('image').file)
        except Exception, e:
            meta.Session.rollback()
            h.flash(unicode(e), 'error')
            log.debug(e)
            return self.edit('category', format=format)

        title, color, visible, description, impact, instance =\
            self._get_common_fields(self.form_result)
        child_descr = self.form_result.get("select_child_description")
        child_descr = child_descr.replace("$badge_title", title)
        long_description = self.form_result.get("long_description", u'')
        # TODO global badges must have only global badges children, joka
        parent = self.form_result.get("parent")
        if parent and parent.id == id:
            parent = None
        badge.title = title
        badge.color = color
        badge.visible = visible
        badge.description = description
        badge.instance = instance
        badge.select_child_description = child_descr
        badge.long_description = long_description
        badge.parent = parent
        if badge.impact != impact:
            badge.impact = impact
            meta.Session.commit()
            for delegateable in badge.delegateables:
                update_entity(delegateable, UPDATE)
        else:
            meta.Session.commit()
        h.flash(_("Badge changed successfully"), 'success')
        self._redirect()

    @RequireInternalRequest()
    def update_thumbnail_badge(self, id, format=u'html'):
        try:
            self.form_result = ThumbnailBadgeForm().to_python(request.params)
        except Invalid as i:
            return self.edit(id, i.unpack_errors(), format=format)
        badge = self._get_badge_or_redirect(id)
        require.badge.edit(badge)
        title, color, visible, description, impact, instance =\
            self._get_common_fields(self.form_result)
        thumbnail = self.form_result.get("thumbnail")
        if isinstance(thumbnail, FieldStorage):
            badge.thumbnail = thumbnail.file.read()
        if 'delete_thumbnail' in self.form_result:
            badge.thumbnail = None
        badge.title = title
        badge.color = color
        badge.visible = visible
        badge.description = description
        badge.instance = instance
        if badge.impact != impact:
            badge.impact = impact
            meta.Session.commit()
            for delegateable in badge.delegateables:
                update_entity(delegateable, UPDATE)
        else:
            meta.Session.commit()
        h.flash(_("Badge changed successfully"), 'success')
        self._redirect()

    def ask_delete(self, id, format=u'html'):
        badge = self._get_badge_or_redirect(id)
        require.badge.manage(badge)

        data = {
            'badge': badge,
            'badge_type': self._get_badge_type(badge),
            'badged_entities': badge.badged_entities(),
        }
        if not c.came_from:
            c.came_from = self.base_url

        return render('/badge/ask_delete.html', data,
                      overlay=format == u'overlay')

    @RequireInternalRequest()
    def delete(self, id, format=u'html'):
        badge = self._get_badge_or_redirect(id)
        require.badge.manage(badge)

        for badge_instance in badge.badges():
            meta.Session.delete(badge_instance)
            update_entity(badge_instance.badged_entity(), UPDATE)
        meta.Session.delete(badge)
        meta.Session.commit()
        h.flash(_(u"Badge deleted successfully"), 'success')
        self._redirect()
