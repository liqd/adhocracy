import logging

from babel import Locale

import formencode
from formencode import htmlfill
from formencode import validators

from paste.deploy.converters import asbool, asint

from pylons import request, response, tmpl_context as c, config
from pylons.controllers.util import abort, redirect
from pylons.decorators import validate
from pylons.i18n import _, lazy_ugettext as L_

from adhocracy import forms, i18n, model
from adhocracy.controllers.admin import AdminController, UserImportForm
from adhocracy.controllers.badge import BadgeController
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib import event, helpers as h, logo, pager, sorting, tiles
from adhocracy.lib.auth import can, csrf, require, guard
from adhocracy.lib.base import BaseController
from adhocracy.lib.queue import update_entity
from adhocracy.lib.templating import (render, render_json, render_png,
                                      ret_abort, ret_success, render_def)
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


class InstanceBadgesForm(formencode.Schema):
    allow_extra_fields = True
    badge = formencode.foreach.ForEach(forms.ValidInstanceBadge())


class InstanceCreateForm(formencode.Schema):
    allow_extra_fields = True
    key = formencode.All(validators.String(min=4, max=20),
                         forms.UniqueInstanceKey())
    label = validators.String(min=4, max=254, not_empty=True)
    description = validators.String(max=100000, if_empty=None, not_empty=False)


class InstanceGeneralEditForm(formencode.Schema):
    allow_extra_fields = True
    label = validators.String(min=4, max=254, not_empty=True)
    description = validators.String(max=100000, if_empty=None, not_empty=False)
    locale = validators.String(not_empty=False)
    default_group = forms.ValidInstanceGroup(not_empty=True)
    hidden = validators.StringBool(not_empty=False, if_empty=False,
                                   if_missing=False)
    require_valid_email = validators.StringBool(not_empty=False,
                                                if_empty=False,
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
    hide_global_categories = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    editable_comments_default = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)


class InstanceVotingEditForm(formencode.Schema):
    allow_extra_fields = True
    allow_adopt = validators.StringBool(not_empty=False, if_empty=False,
                                        if_missing=False)
    allow_delegate = validators.StringBool(not_empty=False, if_empty=False,
                                           if_missing=False)
    activation_delay = validators.Int(not_empty=True)
    required_majority = validators.Number(not_empty=True)
    votedetail_badges = forms.ValidUserBadges()


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

    def index(self, format="html"):
        require.instance.index()

        c.active_global_nav = 'instances'
        c.instance_pager = pager.solr_instance_pager()

        if format == 'json':
            return render_json(c.instance_pager)

        c.tile = tiles.instance.InstanceTile(c.instance)
        return render("/instance/index.html")

    def new(self):
        require.instance.create()

        data = {}
        protocol = config.get('adhocracy.protocol', 'http').strip()
        domain = config.get('adhocracy.domain').strip()

        if asbool(config.get('adhocracy.relative_urls', 'false')):
            data['url_pre'] = '%s://%s/i/' % (protocol, domain)
            data['url_post'] = ''
            data['url_right_align'] = False
        else:
            data['url_pre'] = '%s://' % protocol
            data['url_post'] = '.%s' % domain
            data['url_right_align'] = True

        return render("/instance/new.html", data)

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
        return ret_success(
            message=_('Instance created successfully. You can now configure it'
                      ' as you like.'), category='success',
            entity=instance, member='settings', format=None)

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
        c.sidebar_delegations = (_('Delegations are enabled.') if
                                 c.page_instance.allow_delegate else
                                 _('Delegations are disabled.'))

        if asbool(config.get('adhocracy.show_instance_overview_milestones')) \
                and c.page_instance.milestones:

            number = asint(config.get(
                'adhocracy.number_instance_overview_milestones', 3))

            milestones = model.Milestone.all_future_q(
                instance=c.page_instance).limit(number).all()

            c.next_milestones_pager = pager.milestones(
                milestones, size=number, enable_sorts=False,
                enable_pages=False, default_sort=sorting.milestone_time)

        c.events_pager = None
        if asbool(config.get('adhocracy.show_instance_overview_events',
                             'true')):
            events = model.Event.find_by_instance(c.page_instance, limit=3)
            c.events_pager = pager.events(events,
                                          enable_pages=False,
                                          enable_sorts=False)

        proposals = model.Proposal.all(instance=c.page_instance)

        show_new_proposals_cfg = config.get(
            'adhocracy.show_instance_overview_proposals_new')
        if show_new_proposals_cfg is None:
            # Fall back to legacy option
            show_new_proposals = asbool(config.get(
                'adhocracy.show_instance_overview_proposals', 'true'))
        else:
            show_new_proposals = asbool(show_new_proposals_cfg)
        c.new_proposals_pager = None
        if asbool(show_new_proposals):
            c.new_proposals_pager = pager.proposals(
                proposals, size=7, enable_sorts=False,
                enable_pages=False, default_sort=sorting.entity_newest)

        c.all_proposals_pager = None
        if asbool(config.get('adhocracy.show_instance_overview_proposals_all',
                             'false')):
            c.all_proposals_pager = pager.proposals(proposals)

        c.stats = None
        if asbool(config.get('adhocracy.show_instance_overview_stats',
                             'true')):
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
                                  h.base_url(),
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
    def _editable_badges(cls, instance):
        '''
        Return the badges editable that can be assigned by the current
        user.
        '''
        badges = []
        if can.badge.edit_global():
            badges.extend(model.InstanceBadge.all(instance=None))
        badges = sorted(badges, key=lambda badge: badge.title)
        return badges

    @guard.perm("global.admin")
    def badges(self, id, errors=None, format='html'):
        instance = get_entity_or_abort(model.Instance, id)
        c.badges = self._editable_badges(instance)
        defaults = {
            'badge': [str(badge.id) for badge in instance.badges],
            '_tok': csrf.token_id(),
        }
        if format == 'ajax':
            checked = [badge.id for badge in instance.badges]
            json = {'title': instance.label,
                    'badges': [{
                        'id': badge.id,
                        'description': badge.description,
                        'title': badge.title,
                        'checked': badge.id in checked} for badge in c.badges]}
            return render_json(json)

        return formencode.htmlfill.render(
            render("/instance/badges.html"),
            defaults=defaults)

    @validate(schema=InstanceBadgesForm(), form='badges')
    @guard.perm("global.admin")
    @csrf.RequireInternalRequest(methods=['POST'])
    def update_badges(self, id, format='html'):
        instance = get_entity_or_abort(model.Instance, id)
        editable_badges = self._editable_badges(instance)
        badges = self.form_result.get('badge')
        #remove badges
        for badge in instance.badges:
            if badge not in editable_badges:
                # the user can not edit the badge, so we don't remove it
                continue
            if badge not in badges:
                instance.badges.remove(badge)
        #add badges
        for badge in badges:
            if badge not in instance.badges:
                badge.assign(instance, c.user)

        model.meta.Session.commit()
        update_entity(instance, model.update.UPDATE)
        if format == 'ajax':
            obj = {'html': render_def('/badge/tiles.html', 'badges',
                                      badges=instance.badges)}
            return render_json(obj)

    @classmethod
    def settings_menu(cls, instance, current):

        class Menu(list):
            '''Subclass so we can attach attributes'''

            def url_for(self, value):
                current = [i for i in self if i['name'] == value]
                if not current:
                    return ValueError('No Menu item named "%s"' % value)
                else:
                    return current[0]['url']

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
            setting('massmessage', L_('Mass message service'),
                    allowed=(can.message.create(instance))),
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
        c.active_subheader_nav = 'settings'

        return settings

    def settings_result(self, updated, instance, setting_name, message=None):
        '''
        Sets a redirect code and location header, stores a flash
        message and returns the message. If *message* is not None, a
        message is choosen depending on the boolean value of
        *updated*. The redirect *location* URL is choosen based on the
        instance and *setting_name*.

        This method will *not raise an redirect exception* but set the
        headers and return the message string.

        *updated* (bool)
           Indicate that a value was updated. Used to choose a generic
           message if *message* is not given explicitly.
        *instance* (:class:`adhocracy.model.Instance`)
           The instance to generate the redirct URL for.
        *setting_name* (str)
           The setting name for which the URL will be build.
        *message* (unicode)
           An explicit message to use instead of the generic message.

        Returns
           The message generated or given.
        '''
        if updated:
            event.emit(event.T_INSTANCE_EDIT, c.user, instance=c.page_instance)
            message = message if message else INSTANCE_UPDATED_MSG
            category = 'success'
        else:
            message = message if message else NO_UPDATE_REQUIRED
            category = 'notice'
        h.flash(message, category=category)
        response.status_int = 303
        url = self.settings_menu(instance, setting_name).url_for(setting_name)
        response.headers['location'] = url
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
        (path, mtime, io) = logo.load(id, size=(x, y))
        request_mtime = int(request.params.get('t', 0))
        if request_mtime != mtime:
            instance = get_entity_or_abort(model.Instance, id,
                                           instance_filter=False)
            redirect(h.instance.icon_url(instance, y, x=x))
        return render_png(io, mtime, cache_forever=True)

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
                'require_valid_email': c.page_instance.require_valid_email,
                '_tok': csrf.token_id()})

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=InstanceGeneralEditForm(), form="settings_general_form",
              post_only=True, auto_error_formatter=formatter)
    def settings_general_update(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)

        updated = update_attributes(c.page_instance, self.form_result,
                                    ['description', 'label', 'hidden',
                                     'require_valid_email'])
        if h.has_permission('global.admin'):
            auth_updated = update_attributes(c.page_instance, self.form_result,
                                             ['is_authenticated'])
            updated = updated or auth_updated

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
        c.current_logo = None
        if tiles.instance.InstanceTile(c.page_instance).show_icon():
            c.current_logo = h.instance.icon_url(c.page_instance, 48)

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

        # delete the logo if the button was pressed and exit
        if 'delete_logo' in self.form_result:
            logo.delete(c.page_instance)
            return self.settings_result(
                True, c.page_instance, 'appearance',
                message=_(u'The logo has been deleted.'))

        # process the normal form
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
                'hide_global_categories': instance.hide_global_categories,
                'editable_comments_default': instance.editable_comments_default,
                'frozen': instance.frozen,
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
            ['allow_propose', 'allow_index', 'frozen', 'milestones',
             'use_norms', 'require_selection', 'hide_global_categories',
             'editable_comments_default'])
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
        if model.votedetail.is_enabled():
            c.votedetail_all_userbadges = model.UserBadge.all(
                instance=c.page_instance, include_global=True)
        else:
            c.votedetail_all_userbadges = None

        return render("/instance/settings_voting.html")

    @RequireInstance
    def settings_voting(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)
        defaults = {
            '_method': 'PUT',
            'required_majority': c.page_instance.required_majority,
            'activation_delay': c.page_instance.activation_delay,
            'allow_adopt': c.page_instance.allow_adopt,
            'allow_delegate': c.page_instance.allow_delegate,
            '_tok': csrf.token_id()}
        if model.votedetail.is_enabled():
            defaults['votedetail_badges'] = [
                b.id for b in c.page_instance.votedetail_userbadges]
        return htmlfill.render(
            self.settings_voting_form(id),
            defaults=defaults)

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

        if model.votedetail.is_enabled():
            new_badges = self.form_result['votedetail_badges']
            updated_vd = c.page_instance.votedetail_userbadges != new_badges
            if updated_vd:
                c.page_instance.votedetail_userbadges = new_badges
            updated = updated or updated_vd

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
        controller.start_response = self.start_response
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
        return controller.update(badge_id)

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

        path = request.params.get('came_from', None)

        return ret_success(entity=c.page_instance, format=format,
                           message=_("Welcome to %(instance)s") % {
                               'instance': c.page_instance.label
                           },
                           category='success',
                           force_path=path)

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

    @classmethod
    def _get_current_instance(cls, id):
        if id != c.instance.key:
            abort(403, _("You cannot manipulate one instance from within "
                         "another instance."))
        return c.instance
