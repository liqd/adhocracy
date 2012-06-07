import logging
import os.path

from babel import Locale

import formencode
from formencode import htmlfill
from formencode import validators

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons.decorators import validate
from pylons.i18n import _, lazy_ugettext as L_

from adhocracy import forms, i18n, model
from adhocracy.controllers.admin import AdminController, UserImportForm
from adhocracy.controllers.badge import BadgeController
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib import event, helpers as h, logo, pager, sorting, tiles
from adhocracy.lib.auth import can, csrf, require
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import (render, render_json, render_png,
                                      ret_abort, ret_success)
from adhocracy.lib.util import get_entity_or_abort


log = logging.getLogger(__name__)
INSTANCE_UPDATED_MSG = L_('The changes where saved.')
NO_UPDATE_REQUIRED = L_('No update required.')


def formatter(error):
    return '<p class="help-block">%s</p>' % error


def settings_url(instance, path):
    full_path = 'settings/%s' % path
    return h.instance.url(instance, member=full_path)


def update_attributes(instance, form_result, attributes):
    '''
    Update the given *attributes* on the *instance* object
    with the values in *form_result* and returns if an attribute
    was updated.

    *instance* (:class:`adhocracy.model.Instance`)
       The Instance to update.
    *form_result* (dict)
       A dict, usually the result of a formencode
       validation.
    *attributes* (`list` of `str`)
       The attributes to update.

    Returns: `True` if one of the *attributes* was updated, `False`
    no attribute needed to be updated.

    Raises:

    *AttributeError*
       If the attribute does not exist on the *instance* object.
    *KeyError*
       If the *form_result* dict has no key with the name of the
       attribute.
    '''
    updated = False
    for attribute in attributes:
        new_value = form_result[attribute]
        current_value = getattr(instance, attribute)
        if new_value != current_value:
            setattr(instance, attribute, new_value)
            updated = True
    return updated


class InstanceCreateForm(formencode.Schema):
    allow_extra_fields = True
    key = formencode.All(validators.String(min=4, max=20),
                              forms.UniqueInstanceKey())
    label = validators.String(min=4, max=254, not_empty=True)
    description = validators.String(max=100000, if_empty=None, not_empty=False)


class InstanceEditForm(formencode.Schema):
    allow_extra_fields = True
    label = validators.String(min=4, max=254, not_empty=True)
    description = validators.String(max=100000, if_empty=None, not_empty=False)
    activation_delay = validators.Int(not_empty=True)
    required_majority = validators.Number(not_empty=True)
    default_group = forms.ValidGroup(not_empty=True)
    locale = validators.String(not_empty=False)
    allow_adopt = validators.StringBool(not_empty=False, if_empty=False,
                                        if_missing=False)
    allow_delegate = validators.StringBool(not_empty=False, if_empty=False,
                                           if_missing=False)
    allow_propose = validators.StringBool(not_empty=False, if_empty=False,
                                          if_missing=False)
    allow_index = validators.StringBool(not_empty=False, if_empty=False,
                                       if_missing=False)
    use_norms = validators.StringBool(not_empty=False, if_empty=False,
                                      if_missing=False)
    require_selection = validators.StringBool(not_empty=False, if_empty=False,
                                              if_missing=False)
    hidden = validators.StringBool(not_empty=False, if_empty=False,
                                   if_missing=False)
    frozen = validators.StringBool(not_empty=False, if_empty=False,
                                   if_missing=False)
    milestones = validators.StringBool(not_empty=False, if_empty=False,
                                   if_missing=False)


class InstanceGeneralEditForm(formencode.Schema):
    allow_extra_fields = True
    label = validators.String(min=4, max=254, not_empty=True)
    description = validators.String(max=100000, if_empty=None, not_empty=False)
    locale = validators.String(not_empty=False)
    default_group = forms.ValidGroup(not_empty=True)
    hidden = validators.StringBool(not_empty=False, if_empty=False,
                                   if_missing=False)
    is_authenticated = validators.StringBool(not_empty=False, if_empty=False,
                                          if_missing=False)


class InstanceAppearanceEditForm(formencode.Schema):
    allow_extra_fields = True
    css = validators.String(max=100000, if_empty=None, not_empty=False)


class InstanceContentsEditForm(formencode.Schema):
    allow_extra_fields = True
    allow_propose = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    allow_index = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    use_norms = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    require_selection = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    frozen = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    milestones = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)


class InstanceVotingEditForm(formencode.Schema):
    allow_extra_fields = True
    allow_adopt = validators.StringBool(not_empty=False, if_empty=False,
                                        if_missing=False)
    allow_delegate = validators.StringBool(not_empty=False, if_empty=False,
                                           if_missing=False)
    activation_delay = validators.Int(not_empty=True)
    required_majority = validators.Number(not_empty=True)


class InstanceBadgesEditForm(formencode.Schema):
    allow_extra_fields = True


class InstanceMembersEditForm(formencode.Schema):
    allow_extra_fields = True
    pass


class InstanceSnameEditForm(formencode.Schema):
    allow_extra_fields = True
    pass


# --[ Controller ]----------------------------------------------------------

class InstanceController(BaseController):

    def index(self, format='html'):
        require.instance.index()
        c.active_global_nav = 'instances'
        h.add_meta("description",
                   _("An index of instances run at this site. "
                     "Select which ones you would like to join "
                     "and participate!"))
        instances = model.Instance.all()

        if format == 'json':
            return render_json(instances)

        c.instances_pager = pager.instances(instances)
        return render("/instance/index.html")

    def new(self):
        require.instance.create()
        return render("/instance/new.html")

    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=InstanceCreateForm(), form="new", post_only=True)
    def create(self, format='html'):
        require.instance.create()
        instance = model.Instance.create(
            self.form_result.get('key'), self.form_result.get('label'),
            c.user, description=self.form_result.get('description'),
            locale=c.locale)
        model.meta.Session.commit()
        event.emit(event.T_INSTANCE_CREATE, c.user, instance=instance)
        return ret_success(entity=instance, format=format)

    #@RequireInstance
    def show(self, id, format='html'):
        c.page_instance = get_entity_or_abort(model.Instance, id)
        require.instance.show(c.page_instance)

        if format == 'json':
            return render_json(c.page_instance)

        if format == 'rss':
            return self.activity(id, format)

        if c.page_instance != c.instance:
            redirect(h.entity_url(c.page_instance))

        c.tile = tiles.instance.InstanceTile(c.page_instance)
        proposals = model.Proposal.all(instance=c.page_instance)
        c.new_proposals_pager = pager.proposals(
            proposals, size=7, enable_sorts=False,
            enable_pages=False, default_sort=sorting.entity_newest)

        c.sidebar_delegations = (_('Delegations are enabled.') if
                                 c.page_instance.allow_delegate else
                                 _('Delegations are disabled.'))
        
        #pages = model.Page.all(instance=c.page_instance,
        #        functions=[model.Page.NORM])
        #c.top_pages_pager = pager.pages(
        #    pages, size=7, enable_sorts=False,
        #    enable_pages=False, default_sort=sorting.norm_selections)
        #tags = model.Tag.popular_tags(limit=40)
        #c.tags = sorted(text.tag_cloud_normalize(tags),
        #                key=lambda (k, c, v): k.name)
        if c.page_instance.milestones:
            c.milestones = model.Milestone.all(instance=c.page_instance)
        c.stats = {
            'comments': model.Comment.all_q().count(),
            'proposals': model.Proposal.all_q(
                instance=c.page_instance).count(),
            'members': model.Membership.all_q().count()
        }
        c.tutorial_intro = _('tutorial_instance_show_intro')
        c.tutorial = 'instance_show'
        return render("/instance/show.html")

    @RequireInstance
    def activity(self, id, format='html'):
        c.page_instance = get_entity_or_abort(model.Instance, id)
        require.instance.show(c.page_instance)

        if format == 'sline':
            ret_abort(u'Sparkline data is not available anymore.', code=410)

        events = model.Event.find_by_instance(c.page_instance, limit=50)

        if format == 'rss':
            return event.rss_feed(events,
                                  _('%s News' % c.page_instance.label),
                                  h.base_url(c.page_instance),
                                  _("News from %s") % c.page_instance.label)

        c.tile = tiles.instance.InstanceTile(c.page_instance)
        c.events_pager = pager.events(events)
        return render("/instance/activity.html")

    @RequireInstance
    def edit(self, id):
        # This is deprecated, but the route is still created as
        # by routes' .resource()
        c.page_instance = self._get_current_instance(id)
        redirect(h.instance.url(c.page_instance, member='settings'))

    def update(self, id, format='html'):
        # This is deprecated, but the route is still created as
        # by routes' .resource()
        return self.edit(id)
        
    @classmethod
    def settings_menu(cls, instance, current):

        class Menu(list):
            '''Subclass so we can attach attributes'''
            pass

        def setting(name, label, allowed=True):
            return {'name': name,
                    'url': settings_url(instance, name),
                    'label': label,
                    'allowed': allowed}

        settings = Menu([
            {'name': 'general',
             'url': h.instance.url(instance, member='settings'),
             'label': L_('General')},
            setting('appearance', L_('Appearance')),
            setting('contents', L_('Contents')),
            setting('voting', L_('Votings')),
            setting('badges', L_('Badges')),
            setting('members_import', L_('Members import'),
                    allowed=(h.has_permission('global.admin') or
                             can.instance.authenticated_edit(instance)))])

        if current not in [i['name'] for i in settings]:
            raise ValueError('current ("%s") is no menu item' % current)

        for item in settings:
            item['class'] = ''
            if item.get('allowed') is None:
                item['allowed'] = True
            if current == item['name']:
                item['active'] = True
                item['class'] = 'active'
                settings.current = item

        return settings

    def settings_result(self, updated, instance, setting_name):
        if updated:
            event.emit(event.T_INSTANCE_EDIT, c.user, instance=c.page_instance)
            message = INSTANCE_UPDATED_MSG
            category = 'success'
        else:
            message = NO_UPDATE_REQUIRED
            category = 'notice'
        h.flash(message, category=category)
        response.status_int = 303
        response.headers['location'] = settings_url(instance, setting_name)
        return unicode(message)

    def icon(self, id, y=24, x=None):
        try:
            y = int(y)
        except ValueError, ve:
            log.debug(ve)
            y = 24
        try:
            x = int(x)
        except:
            x = None
        (path, io) = logo.load(id, size=(x, y))
        return render_png(io, os.path.getmtime(path))

    def settings_general_form(self, id):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = self.settings_menu(c.page_instance, 'general')
        c.locales = []
        for locale in i18n.LOCALES:
            c.locales.append({'value': str(locale),
                              'label': locale.display_name,
                              'selected': locale == c.page_instance.locale})

        c.default_group_options = []
        c.default_group = (c.page_instance.default_group.code if
                           c.page_instance.default_group else
                           model.Group.INSTANCE_DEFAULT)

        for groupname in model.Group.INSTANCE_GROUPS:
            group = model.Group.by_code(groupname)
            c.default_group_options.append(
                {'value': group.code,
                 'label': h.literal(_(group.group_name)),
                 'selected': group.code == c.default_group})

        rendered = render("/instance/settings_general.html")
        return rendered

    @RequireInstance
    def settings_general(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)
        form_content = self.settings_general_form(id)
        return htmlfill.render(
            form_content,
            defaults={
                '_method': 'PUT',
                'label': c.page_instance.label,
                'description': c.page_instance.description,
                'default_group': c.default_group,
                'hidden': c.page_instance.hidden,
                'locale': c.page_instance.locale,
                'is_authenticated': c.page_instance.is_authenticated,
                '_tok': csrf.token_id()})

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=InstanceGeneralEditForm(), form="settings_general_form",
              post_only=True, auto_error_formatter=formatter)
    def settings_general_update(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)

        updated = update_attributes(c.page_instance, self.form_result,
                                    ['description', 'label', 'hidden'])
        if h.has_permission('global.admin'):
            auth_updated = update_attributes(c.page_instance, self.form_result,
                                             ['is_authenticated'])
            updated = updated or auth_updated

        if (self.form_result.get('default_group').code in
            model.Group.INSTANCE_GROUPS):
            updated = updated or update_attributes(c.page_instance,
                                                   self.form_result,
                                                   ['default_group'])
        locale = Locale(self.form_result.get("locale"))
        if locale and locale in i18n.LOCALES:
            if c.page_instance.locale != locale:
                c.page_instance.locale = locale
                updated = True

        return self.settings_result(updated, c.page_instance, 'general')

    def settings_appearance_form(self, id):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = self.settings_menu(c.page_instance, 'appearance')
        return render("/instance/settings_appearance.html")

    @RequireInstance
    def settings_appearance(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)
        return htmlfill.render(
            self.settings_appearance_form(id),
            defaults={
                '_method': 'PUT',
                'css': c.page_instance.css,
                '_tok': csrf.token_id()})

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=InstanceAppearanceEditForm(),
              form="settings_appearance_form",
              post_only=True, auto_error_formatter=formatter)
    def settings_appearance_update(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)

        updated = update_attributes(c.page_instance, self.form_result, ['css'])
        try:
            # fixme: show logo errors in the form
            if ('logo' in request.POST and
                hasattr(request.POST.get('logo'), 'file') and
                request.POST.get('logo').file):
                logo.store(c.page_instance, request.POST.get('logo').file)
                updated = True
        except Exception, e:
            model.meta.Session.rollback()
            h.flash(unicode(e), 'error')
            log.debug(e)
            return self.settings_appearance(id)

        return self.settings_result(updated, c.page_instance, 'appearance')

    def settings_contents_form(self, id):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = self.settings_menu(c.page_instance, 'contents')
        return render("/instance/settings_contents.html")

    @RequireInstance
    def settings_contents(self, id):
        instance = self._get_current_instance(id)
        require.instance.edit(instance)
        c.page_instance = instance
        return htmlfill.render(
            self.settings_contents_form(id),
            defaults={
                '_method': 'PUT',
                'allow_propose': instance.allow_propose,
                'milestones': instance.milestones,
                'use_norms': instance.use_norms,
                'require_selection': instance.require_selection,
                '_tok': csrf.token_id()})

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=InstanceContentsEditForm(),
              form="settings_contents_form",
              post_only=True)
    def settings_contents_update(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)

        updated = update_attributes(
            c.page_instance, self.form_result,
            ['allow_propose', 'allow_index',
             'milestones', 'use_norms', 'require_selection'])
        return self.settings_result(updated, c.page_instance, 'contents')

    def settings_voting_form(self, id):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = self.settings_menu(c.page_instance, 'voting')
        c.delay_options = []
        for delay in ((0, _("No delay")),
                      (1, _("1 Day")),
                      (2, _("2 Days")),
                      (7, _("One Week")),
                      (14, _("Two Weeks")),
                      (28, _("Four Weeks"))):
            c.delay_options.append(
                {'value': delay[0],
                 'label': h.literal(delay[1]),
                 'selected': c.page_instance.activation_delay == delay[0]})
        c.majority_options = []
        for majority in ((0.5, _("A simple majority (&frac12; of vote)")),
                         (0.66, _("A two-thirds majority"))):
            c.majority_options.append(
                {'value': majority[0],
                 'label': h.literal(majority[1]),
                 'selected': c.page_instance.required_majority == majority[0]})
        return render("/instance/settings_voting.html")

    @RequireInstance
    def settings_voting(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)
        return htmlfill.render(
            self.settings_voting_form(id),
            defaults={
                '_method': 'PUT',
                'required_majority': c.page_instance.required_majority,
                'activation_delay': c.page_instance.activation_delay,
                'allow_adopt': c.page_instance.allow_adopt,
                'allow_delegate': c.page_instance.allow_delegate,
                '_tok': csrf.token_id()})

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=InstanceVotingEditForm(),
              form="settings_voting_form",
              post_only=True, auto_error_formatter=formatter)
    def settings_voting_update(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)

        updated = update_attributes(
            c.page_instance, self.form_result,
            ['required_majority', 'activation_delay', 'allow_adopt',
             'allow_delegate'])
        return self.settings_result(updated, c.page_instance, 'voting')

    def badge_controller(self, instance):
        '''
        ugly hack to dispatch to the badge controller.
        '''
        controller = BadgeController()
        controller.index_template = 'instance/settings_badges.html'
        controller.form_template = 'instance/settings_badges_form.html'
        controller.base_url_ = settings_url(instance, 'badges')
        controller._py_object = self._py_object
        return controller

    @RequireInstance
    def settings_badges(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)
        c.settings_menu = self.settings_menu(c.page_instance, 'badges')
        controller = self.badge_controller(c.page_instance)
        return controller.index()

    @RequireInstance
    def settings_badges_add(self, id, badge_type):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = self.settings_menu(c.page_instance, 'badges')
        controller = self.badge_controller(c.page_instance)
        return controller.add(badge_type=badge_type)

    @RequireInstance
    def settings_badges_create(self, id, badge_type):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = self.settings_menu(c.page_instance, 'badges')
        controller = self.badge_controller(c.page_instance)
        return controller.create(badge_type=badge_type)

    @RequireInstance
    def settings_badges_edit(self, id, badge_id):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = self.settings_menu(c.page_instance, 'badges')
        controller = self.badge_controller(c.page_instance)
        return controller.edit(badge_id)

    @RequireInstance
    def settings_badges_update(self, id, badge_id):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = self.settings_menu(c.page_instance, 'badges')
        controller = self.badge_controller(c.page_instance)
        return controller.add(badge_id)

    def settings_members_import_form(self, id):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = self.settings_menu(c.page_instance, 'members_import')
        return render("/instance/settings_members_import.html")

    @RequireInstance
    def settings_members_import(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)
        return htmlfill.render(
            self.settings_members_import_form(id),
            defaults={
                '_method': 'PUT',
                '_tok': csrf.token_id()})

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=UserImportForm(),
              form="settings_members_import_form",
              post_only=True, auto_error_formatter=formatter)
    def settings_members_import_save(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = self.settings_menu(c.page_instance, 'members_import')
        require.instance.edit(c.page_instance)
        AdminController()._create_users(self.form_result)
        return(render("/instance/settings_members_import_success.html"))

# --[ template ]------------------------------------------------------------

    def settings_sname_form(self, id):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = self.settings_menu(c.page_instance, 'sname')
        return render("/instance/settings_sname.html")

    @RequireInstance
    def settings_sname(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)
        return htmlfill.render(
            self.settings_sname_form(id),
            defaults={
                '_method': 'PUT',
                '_tok': csrf.token_id()})

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=InstanceSnameEditForm(),
              form="settings_sname_form",
              post_only=True, auto_error_formatter=formatter)
    def settings_sname_update(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)

        updated = update_attributes(c.page_instance, self.form_result, [])
        return self.settings_result(updated, c.page_instance, 'sname')

    @RequireInstance
    def style(self, id):
        c.page_instance = self._get_current_instance(id)
        response.content_type = 'text/css'
        if c.page_instance.css:
            return c.page_instance.css
        return ''

    @RequireInstance
    def ask_delete(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.delete(c.page_instance)
        c.tile = tiles.instance.InstanceTile(c.page_instance)
        return render('/instance/ask_delete.html')

    @csrf.RequireInternalRequest()
    def delete(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.delete(c.page_instance)
        c.page_instance.delete()
        model.meta.Session.commit()
        event.emit(event.T_INSTANCE_DELETE, c.user, instance=c.instance,
                   topics=[])
        return ret_success(format=format,
                           message=_("The instance %s has been deleted.") %
                           c.page_instance.label)

    @RequireInstance
    @csrf.RequireInternalRequest()
    def join(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.join(c.page_instance)

        membership = model.Membership(c.user, c.page_instance,
                                      c.page_instance.default_group)
        model.meta.Session.expunge(membership)
        model.meta.Session.add(membership)
        model.meta.Session.commit()

        event.emit(event.T_INSTANCE_JOIN, c.user,
                   instance=c.page_instance)

        return ret_success(entity=c.page_instance, format=format,
                           message=_("Welcome to %(instance)s") % {
                            'instance': c.page_instance.label},
                            category='success')

    def ask_leave(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.leave(c.page_instance)

        c.tile = tiles.instance.InstanceTile(c.page_instance)
        return render('/instance/ask_leave.html')

    @csrf.RequireInternalRequest(methods=['POST'])
    def leave(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        if not c.page_instance in c.user.instances:
            return ret_abort(
                entity=c.page_instance, format=format,
                message=_("You're not a member of %(instance)s.") % {
                                    'instance': c.page_instance.label})
        elif c.user == c.page_instance.creator:
            return ret_abort(
                entity=c.page_instance, format=format,
                message=_("You're the founder of %s, cannot leave.") % {
                                    'instance': c.page_instance.label})
        require.instance.leave(c.page_instance)

        for membership in c.user.memberships:
            if membership.is_expired():
                continue
            if membership.instance == c.page_instance:
                membership.expire()
                model.meta.Session.add(membership)

                c.user.revoke_delegations(c.page_instance)

                event.emit(event.T_INSTANCE_LEAVE, c.user,
                           instance=c.page_instance)
        model.meta.Session.commit()
        return ret_success(entity=c.page_instance, format=format,
                           message=_("You've left %(instance)s.") % {
                                'instance': c.page_instance.label})

    def _get_current_instance(self, id):
        if id != c.instance.key:
            abort(403, _("You cannot manipulate one instance from within "
                         "another instance."))
        return c.instance
