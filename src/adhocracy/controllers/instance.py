from collections import OrderedDict
import logging

from webob.multidict import MultiDict

import formencode
from formencode import htmlfill
from formencode import validators

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons.decorators import validate
from pylons.i18n import _

from sqlalchemy import func
import geojson

from adhocracy import config
from adhocracy import forms, i18n, model
from adhocracy.controllers.admin import UserImportForm
from adhocracy.controllers.badge import BadgeController
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib import event, helpers as h, logo, pager, sorting, tiles
from adhocracy.lib import cache
from adhocracy.lib import votedetail
from adhocracy.lib.settings import INSTANCE_UPDATED_MSG
from adhocracy.lib.settings import NO_UPDATE_REQUIRED
from adhocracy.lib.settings import error_formatter
from adhocracy.lib.settings import Menu
from adhocracy.lib.settings import update_attributes
from adhocracy.lib.auth import can, csrf, require, guard
from adhocracy.lib.base import BaseController
from adhocracy.lib.queue import update_entity
from adhocracy.lib.staticpage import get_static_page
from adhocracy.lib.staticpage import render_body
from adhocracy.lib.templating import (render, render_json, render_logo,
                                      ret_abort, ret_success, render_def)
from adhocracy.lib.templating import render_geojson
from adhocracy.lib.templating import set_json_response
from adhocracy.lib.templating import OVERLAY_SMALL
from adhocracy.lib.user_import import user_import, get_user_import_state
from adhocracy.lib.util import get_entity_or_abort
from adhocracy.lib.geo import add_instance_props
from adhocracy.lib.geo import get_instance_geo_centre

log = logging.getLogger(__name__)


PRESETS = {
    'agenda_setting': set((
        'allow_delegate',
        'show_proposals_navigation',
    )),
    'consultation': set((
        'use_norms',
        'show_norms_navigation',
    )),
    'planning_ideas': set((
        'allow_delegate',
        'milestones',
    )),
    'locating_ideas': set((
        'allow_delegate',
        'use_maps',
    )),
    'land_use': set((
        'use_norms',
        'use_maps',
    )),
    # Only settings which are part of at least one preset will be changed.
    # Add settings to this pseudo-preset to disable it on every reset
    'always_off': set((
        'hide_global_categories',
        'display_category_pages',
        'allow_propose',
        'allow_propose_changes',
        'require_selection',
    )),
}


def settings_url(instance, path):
    full_path = 'settings/%s' % path
    return h.instance.url(instance, member=full_path)


def settings_menu(instance, current):

    return Menu.create(instance, current, OrderedDict([
        ('overview', (_(u'Overview'),)),
        ('general', (_('General settings'),)),
        ('process', (_('Process settings'),)),
        ('members', (_('Manage members'),)),
        ('advanced', (_('Advanced settings'),)),
        ('presets', (_('Process presets'),)),
    ]))


class InstanceBadgesForm(formencode.Schema):
    allow_extra_fields = True
    badge = formencode.foreach.ForEach(forms.ValidInstanceBadge())


class InstanceCreateForm(formencode.Schema):
    allow_extra_fields = True
    key = formencode.All(
        validators.String(
            min=config.get_int('adhocracy.instance_key_length_min'),
            max=config.get_int('adhocracy.instance_key_length_max')),
        forms.UniqueInstanceKey())
    label = validators.String(min=4, max=254, not_empty=True)
    description = validators.String(max=100000, if_empty=None, not_empty=False)


class InstanceOverviewEditForm(formencode.Schema):
    allow_extra_fields = True
    label = validators.String(min=4, max=254, not_empty=True)
    description = validators.String(max=100000, if_empty=None, not_empty=False)
    logo_as_background = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)


class InstanceGeneralEditForm(formencode.Schema):
    allow_extra_fields = True
    allow_delegate = validators.StringBool(not_empty=False, if_empty=False,
                                           if_missing=False)
    milestones = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    display_category_pages = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    locale = forms.ValidLocale()
    theme = validators.String(not_empty=False, if_empty=None, if_missing=None)


class InstanceProcessEditForm(formencode.Schema):
    allow_extra_fields = True
    allow_propose = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    allow_propose_changes = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    use_maps = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    show_norms_navigation = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    show_proposals_navigation = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    use_norms = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    region_id = forms.ValidRegion(not_empty=False, if_empty=None,
                                  if_missing=None)


class InstanceMembersEditForm(formencode.Schema):
    allow_extra_fields = True
    require_valid_email = validators.StringBool(not_empty=False,
                                                if_empty=False,
                                                if_missing=False)
    default_group = forms.ValidInstanceGroup(not_empty=True)


class InstanceAdvancedEditForm(formencode.Schema):
    allow_extra_fields = True
    editable_comments_default = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    editable_proposals_default = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    require_selection = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    hide_global_categories = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    page_index_as_tiles = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    votedetail_badges = forms.ValidUserBadges()
    hidden = validators.StringBool(not_empty=False, if_empty=False,
                                   if_missing=False)
    # currently no ui
    # allow_index = validators.StringBool(
    #     not_empty=False, if_empty=False, if_missing=False)
    frozen = validators.StringBool(
        not_empty=False, if_empty=False, if_missing=False)
    css = validators.String(max=100000, if_empty=None, not_empty=False,
                            if_missing=None)
    thumbnailbadges_width = validators.Int(not_empty=False, if_empty=None,
                                           if_missing=None)
    thumbnailbadges_height = validators.Int(not_empty=False, if_empty=None,
                                            if_missing=None)
    is_authenticated = validators.StringBool(not_empty=False, if_empty=False,
                                             if_missing=False)


class InstanceBadgesEditForm(formencode.Schema):
    allow_extra_fields = True


class InstanceSnameEditForm(formencode.Schema):
    allow_extra_fields = True
    pass


class InstancePresetsForm(formencode.Schema):
    allow_extra_fields = True
    agenda_setting = validators.StringBool(not_empty=False, if_empty=False,
                                           if_missing=False)
    consultation = validators.StringBool(not_empty=False, if_empty=False,
                                         if_missing=False)
    chained_validators = [
        forms.common.NotAllFalse(PRESETS.keys(),
                                 _(u"Please select at least one preset")),
    ]


# --[ Controller ]----------------------------------------------------------

class InstanceController(BaseController):

    identifier = 'instances'

    @guard.instance.index()
    def index(self, format="html"):

        c.active_global_nav = 'instances'

        include_hidden = h.has_permission('global.admin')
        c.instance_pager = pager.solr_instance_pager(include_hidden)

        if format == 'json':
            return render_json(c.instance_pager)

        c.tile = tiles.instance.InstanceTile(c.instance)
        if format == 'overlay':
            return render("/instance/index.html", overlay=True)
        else:
            return render("/instance/index.html")

    @guard.instance.create()
    def new(self, format=u'html'):

        data = {}
        protocol = config.get('adhocracy.protocol').strip()
        domain = config.get('adhocracy.domain').strip()

        if config.get_bool('adhocracy.relative_urls'):
            data['url_pre'] = '%s://%s/i/' % (protocol, domain)
            data['url_post'] = ''
            data['url_right_align'] = False
        else:
            data['url_pre'] = '%s://' % protocol
            data['url_post'] = '.%s' % domain
            data['url_right_align'] = True

        return render("/instance/new.html", data,
                      overlay=format == u'overlay')

    @csrf.RequireInternalRequest(methods=['POST'])
    @guard.instance.create()
    @validate(schema=InstanceCreateForm(), form="new", post_only=True)
    def create(self, format='html'):
        instance = model.Instance.create(
            self.form_result.get('key'), self.form_result.get('label'),
            c.user, description=self.form_result.get('description'),
            locale=c.locale)
        model.meta.Session.commit()
        event.emit(event.T_INSTANCE_CREATE, c.user, instance=instance)
        return redirect(h.entity_url(instance, member='presets'))

    # @RequireInstance
    def show(self, id, format='html'):
        c.page_instance = get_entity_or_abort(model.Instance, id)
        require.instance.show(c.page_instance)

        if format == 'json':
            return render_json(c.page_instance)
        elif format == 'rss':
            return self.activity(id, format)

        if c.page_instance != c.instance:
            redirect(h.entity_url(c.page_instance))

        static_path = config.get(
            'adhocracy.instance-%s.static_overview_path' % c.page_instance.key,
            None)
        if static_path is not None:
            page = get_static_page(static_path)
            if page is None:
                return abort(404, _('The requested page was not found'))
            data = {
                'static': page,
                'body_html': render_body(page.body),
                'full_width': True,
            }
            c.body_css_classes += page.css_classes
            return render("/static/show.html", data,
                          overlay=format == 'overlay')

        c.tile = tiles.instance.InstanceTile(c.page_instance)
        c.sidebar_delegations = (_('Delegations are enabled.') if
                                 c.page_instance.allow_delegate else
                                 _('Delegations are disabled.'))

        overview_contents = config.get_list(
            'adhocracy.instance_overview_contents')
        overview_sidebar_contents = config.get_list(
            'adhocracy.instance_overview_sidebar_contents')

        if u'milestones' in overview_contents and c.page_instance.milestones:

            number = config.get_int(
                'adhocracy.number_instance_overview_milestones')

            milestones = model.Milestone.all_future_q(
                instance=c.page_instance).limit(number).all()

            c.next_milestones_pager = pager.milestones(
                milestones, size=number, enable_sorts=False,
                enable_pages=False, default_sort=sorting.milestone_time)

        c.events_pager = None
        if u'events' in overview_contents:
            events = model.Event.find_by_instance(c.page_instance, limit=10)
            c.events_pager = pager.events(events,
                                          enable_pages=False,
                                          enable_sorts=False)

        c.sidebar_events_pager = None
        if u'events' in overview_sidebar_contents:
            events = model.Event.find_by_instance(c.page_instance, limit=3)
            c.sidebar_events_pager = pager.events(events,
                                                  enable_pages=False,
                                                  enable_sorts=False,
                                                  row_type=u'sidebar_row')

        c.proposals_pager = None
        if u'proposals' in overview_contents:
            proposals = model.Proposal.all(instance=c.page_instance)

            if config.get_bool(
                    'adhocracy.show_instance_overview_proposals_all'):
                c.proposals_pager = pager.proposals(proposals, size=100,
                                                    initial_size=100)
            else:
                c.proposals_pager = pager.proposals(
                    proposals, size=7, enable_sorts=False,
                    enable_pages=False, default_sort=sorting.entity_newest)

        c.stats = None
        if config.get_bool('adhocracy.show_instance_overview_stats'):
            c.stats = {
                'comments': model.Comment.all_q().count(),
                'proposals': model.Proposal.all_q(
                    instance=c.page_instance).count(),
                'members': model.Membership.all_q().count()
            }

        c.tutorial_intro = _('tutorial_instance_show_intro')
        c.tutorial = 'instance_show'

        if c.page_instance.hidden:
            h.flash(_(u"This instance is not yet open for public "
                      u"participation."), 'warning')
        elif c.page_instance.frozen:
            h.flash(_(u"This instance is not active for use and is archived. "
                      u"It isn't possible to perform any changes to the "
                      u"instance, but all content is available to be read."),
                    'warning')

        if format == 'overlay':
            return render("/instance/show.html", overlay=True)
        else:
            return render("/instance/show.html")

    @RequireInstance
    def activity(self, id, format='html'):
        """ deprecated in favour of /event/all """
        return redirect(h.base_url('/event/all.' + format,
                                   query_params=request.params),
                        code=301)

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
        c.page_instance = get_entity_or_abort(model.Instance, id)
        c.badges = self._editable_badges(c.page_instance)
        defaults = {
            'badge': [str(badge.id) for badge in c.page_instance.badges],
            '_tok': csrf.token_id(),
        }
        if format == 'ajax':
            checked = [badge.id for badge in c.page_instance.badges]
            json = {'title': c.page_instance.label,
                    'badges': [{
                        'id': badge.id,
                        'description': badge.description,
                        'title': badge.title,
                        'checked': badge.id in checked} for badge in c.badges]}
            return render_json(json)
        else:
            return formencode.htmlfill.render(
                render("/instance/badges.html", overlay=format == u'overlay',
                       overlay_size=OVERLAY_SMALL),
                defaults=defaults)

    @validate(schema=InstanceBadgesForm(), form='badges')
    @guard.perm("global.admin")
    @csrf.RequireInternalRequest(methods=['POST'])
    def update_badges(self, id, format='html'):
        instance = get_entity_or_abort(model.Instance, id)
        editable_badges = self._editable_badges(instance)
        badges = self.form_result.get('badge')
        # remove badges
        for badge in instance.badges:
            if badge not in editable_badges:
                # the user can not edit the badge, so we don't remove it
                continue
            if badge not in badges:
                instance.badges.remove(badge)
        # add badges
        for badge in badges:
            if badge not in instance.badges:
                badge.assign(instance, c.user)

        model.meta.Session.commit()
        update_entity(instance, model.UPDATE)
        if format == 'ajax':
            obj = {'html': render_def('/badge/tiles.html', 'badges',
                                      badges=instance.badges)}
            return render_json(obj)

    def _settings_result(self, updated, instance, setting_name, message=None):
        '''
        Sets a redirect code and location header, stores a flash
        message and returns the message. If *message* is not None, a
        message is chosen depending on the boolean value of
        *updated*. The redirect *location* URL is chosen based on the
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
            message = message if message else unicode(INSTANCE_UPDATED_MSG)
            category = 'success'
        else:
            message = message if message else unicode(NO_UPDATE_REQUIRED)
            category = 'notice'
        h.flash(message, category=category)
        response.status_int = 303
        url = settings_menu(instance, setting_name).url_for(setting_name)
        response.headers['location'] = url
        return unicode(message)

    @guard.perm('instance.index')
    def icon(self, id, y=24, x=None):
        instance = get_entity_or_abort(model.Instance, id,
                                       instance_filter=False)
        return render_logo(instance, y, x=x, fallback=logo.INSTANCE)

    @RequireInstance
    def settings_legacy(self, id, format=u'html'):
        instance = self._get_current_instance(id)
        require.instance.edit(instance)
        redirect(h.entity_url(instance, member='settings/overview'), code=301)

    def _settings_overview_form(self, id):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = settings_menu(c.page_instance, 'overview')

        c.current_logo = None
        if tiles.instance.InstanceTile(c.page_instance).show_icon():
            c.current_logo = h.logo_url(c.page_instance, 48)

        return render("/instance/settings_overview.html")

    @RequireInstance
    def settings_overview(self, id, format=u'html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit_overview(c.page_instance)
        form_content = self._settings_overview_form(id)
        return htmlfill.render(
            form_content,
            defaults={
                '_method': 'PUT',
                'label': c.page_instance.label,
                'description': c.page_instance.description,
                'logo_as_background': c.page_instance.logo_as_background,
                '_tok': csrf.token_id()})

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=InstanceOverviewEditForm(),
              form="_settings_overview_form",
              post_only=True, auto_error_formatter=error_formatter)
    def settings_overview_update(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit_overview(c.page_instance)

        # delete the logo if the button was pressed and exit
        if 'delete_logo' in self.form_result:
            updated = logo.delete(c.page_instance)
            return self._settings_result(
                updated, c.page_instance, 'overview',
                message=_(u'The logo has been deleted.'))

        updated = update_attributes(c.page_instance, self.form_result,
                                    ['description', 'label'])

        if c.page_instance.is_authenticated:
            auth_updated = update_attributes(c.page_instance,
                                             self.form_result,
                                             ['logo_as_background'])
            updated = updated or auth_updated

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
            return self.settings_overview(id)

        return self._settings_result(updated, c.page_instance, 'overview')

    def _settings_general_form(self, id):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = settings_menu(c.page_instance, 'general')

        c.locales = []
        for locale in i18n.LOCALES:
            c.locales.append({'value': str(locale),
                              'label': locale.language_name,
                              'selected': locale == c.page_instance.locale})

        return render("/instance/settings_general.html")

    @RequireInstance
    def settings_general(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)
        cat_badge_data = self.badge_controller(c.page_instance, 'general')\
            ._get_badge_data('category')
        c.category_badge_tables = render_def('/badge/index.html',
                                             'render_context_tables',
                                             cat_badge_data)
        theme = '' if c.page_instance.theme is None else c.page_instance.theme

        return htmlfill.render(
            self._settings_general_form(id),
            defaults={
                '_method': 'PUT',
                'allow_delegate': c.page_instance.allow_delegate,
                'milestones': c.page_instance.milestones,
                'display_category_pages':
                c.page_instance.display_category_pages,
                'locale': c.page_instance.locale,
                'theme': theme,
                '_tok': csrf.token_id()})

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=InstanceGeneralEditForm(),
              Form="_settings_general_form",
              post_only=True, auto_error_formatter=error_formatter)
    def settings_general_update(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)

        updated = update_attributes(c.page_instance, self.form_result,
                                    ['allow_delegate', 'locale', 'milestones',
                                     'display_category_pages'])

        stylesheets = config.get_list('adhocracy.instance_stylesheets')
        themes = config.get_list('adhocracy.instance_themes')
        if (c.page_instance.is_authenticated and themes
                and c.page_instance.key not in stylesheets):
            auth_updated = update_attributes(c.page_instance,
                                             self.form_result,
                                             ['theme'])
            updated = updated or auth_updated

        return self._settings_result(updated, c.page_instance, 'general')

    def _settings_process_form(self, id):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = settings_menu(c.page_instance, 'process')

        c.regions = [{
            'value': u'',
            'label': _(u'None'),
            'selected': c.page_instance.region is None,
        }]
        for region in model.meta.Session.query(model.Region).all():
            c.regions.append({'value': str(region.id),
                              'label': region.name,
                              'selected': region == c.page_instance.region})

        return render("/instance/settings_process.html")

    @RequireInstance
    def settings_process(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)
        thumb_badge_data = self.badge_controller(c.page_instance, 'process')\
            ._get_badge_data('thumbnail')
        c.thumbnail_badge_tables = render_def('/badge/index.html',
                                              'render_context_tables',
                                              thumb_badge_data)
        deleg_badge_data = self.badge_controller(c.page_instance, 'process')\
            ._get_badge_data('delegateable')
        c.delegateable_badge_tables = render_def('/badge/index.html',
                                                 'render_context_tables',
                                                 deleg_badge_data)
        return htmlfill.render(
            self._settings_process_form(id),
            defaults={
                '_method': 'PUT',
                'allow_propose': c.page_instance.allow_propose,
                'allow_propose_changes': c.page_instance.allow_propose_changes,
                'show_norms_navigation': c.page_instance.show_norms_navigation,
                'show_proposals_navigation':
                c.page_instance.show_proposals_navigation,
                'use_maps': c.page_instance.use_maps,
                'region_id': c.page_instance.region_id,
                'use_norms': c.page_instance.use_norms,
                '_tok': csrf.token_id()})

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=InstanceProcessEditForm(),
              Form="_settings_process_form",
              post_only=True, auto_error_formatter=error_formatter)
    def settings_process_update(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)

        updated = update_attributes(
            c.page_instance, self.form_result,
            ['allow_propose', 'allow_propose_changes', 'use_norms',
             'show_norms_navigation', 'show_proposals_navigation', 'use_maps',
             'region_id'])

        return self._settings_result(updated, c.page_instance, 'process')

    def _settings_members_form(self, id):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = settings_menu(c.page_instance, 'members')

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

        return render("/instance/settings_members.html")

    @RequireInstance
    def settings_members(self, id):
        c.page_instance = self._get_current_instance(id)
        badge_data = self.badge_controller(c.page_instance, 'members')\
            ._get_badge_data('user')
        c.user_badge_tables = render_def('/badge/index.html',
                                         'render_context_tables',
                                         badge_data)

        require.instance.edit(c.page_instance)
        return htmlfill.render(
            self._settings_members_form(id),
            defaults={
                '_method': 'PUT',
                'require_valid_email': c.page_instance.require_valid_email,
                'default_group': c.default_group,
                '_tok': csrf.token_id()})

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=InstanceMembersEditForm(),
              form="_settings_members_form",
              post_only=True)
    def settings_members_update(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)

        updated = update_attributes(
            c.page_instance, self.form_result, ['require_valid_email',
                                                'default_group'])

        return self._settings_result(updated, c.page_instance, 'members')

    def _settings_advanced_form(self, id):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = settings_menu(c.page_instance, 'advanced')

        if votedetail.is_enabled():
            c.votedetail_all_userbadges = model.UserBadge.all(
                instance=c.page_instance, include_global=True)
        else:
            c.votedetail_all_userbadges = None

        return render("/instance/settings_advanced.html")

    @RequireInstance
    def settings_advanced(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)

        query_params = MultiDict([
            ('event_filter', 't_proposal_create'),
            ('event_filter', 't_page_create'),
            ('event_filter', 't_comment_create'),
        ])
        embed_url = h.base_url('/event/carousel.overlay',
                               query_params=query_params, absolute=True)
        embed_code = ('<iframe src="%s" frameborder="0" width="320"'
                      ' height="320"></iframe>' % embed_url)

        defaults = {
            '_method': 'PUT',
            'editable_comments_default':
            c.page_instance.editable_comments_default,
            'editable_proposals_default':
            c.page_instance.editable_proposals_default,
            'require_selection': c.page_instance.require_selection,
            'hide_global_categories': c.page_instance.hide_global_categories,
            'page_index_as_tiles': c.page_instance.page_index_as_tiles,
            'hidden': c.page_instance.hidden,
            'frozen': c.page_instance.frozen,
            'css': c.page_instance.css,
            'thumbnailbadges_width':
            c.page_instance.thumbnailbadges_width,
            'thumbnailbadges_height':
            c.page_instance.thumbnailbadges_height,
            'is_authenticated': c.page_instance.is_authenticated,
            'embed_code': embed_code,
            '_tok': csrf.token_id()}
        if votedetail.is_enabled():
            defaults['votedetail_badges'] = [
                b.id for b in c.page_instance.votedetail_userbadges]
        return htmlfill.render(
            self._settings_advanced_form(id),
            defaults=defaults)

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=InstanceAdvancedEditForm(),
              form="_settings_advanced_form",
              post_only=True, auto_error_formatter=error_formatter)
    def settings_advanced_update(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)

        updated = update_attributes(
            c.page_instance, self.form_result,
            ['editable_comments_default', 'editable_proposals_default',
             'require_selection', 'hide_global_categories', 'hidden',
             'frozen', 'page_index_as_tiles'])
        # currently no ui for allow_index

        if h.has_permission('global.admin'):
            auth_updated = update_attributes(c.page_instance, self.form_result,
                                             ['css',
                                              'thumbnailbadges_width',
                                              'thumbnailbadges_height',
                                              'is_authenticated'])
            updated = updated or auth_updated

        if votedetail.is_enabled():
            new_badges = self.form_result['votedetail_badges']
            updated_vd = c.page_instance.votedetail_userbadges != new_badges
            if updated_vd:
                c.page_instance.votedetail_userbadges = new_badges
            updated = updated or updated_vd

        return self._settings_result(updated, c.page_instance, 'advanced')

    def badge_controller(self, instance, settings_part):
        '''
        ugly hack to dispatch to the badge controller.
        '''
        controller = BadgeController()
        controller.index_template = 'instance/settings_badges.html'
        controller.form_template = 'instance/settings_badges_form.html'
        controller.base_url_ = settings_url(instance, settings_part)
        controller._py_object = self._py_object
        controller.start_response = self.start_response
        return controller

    @RequireInstance
    def settings_badges_add(self, id, part, badge_type, format='html'):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = settings_menu(c.page_instance, part)
        controller = self.badge_controller(c.page_instance, part)
        return controller.add(badge_type=badge_type, format=format)

    @RequireInstance
    def settings_badges_create(self, id, part, badge_type, format='html'):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = settings_menu(c.page_instance, part)
        controller = self.badge_controller(c.page_instance, part)
        return controller.create(badge_type=badge_type, format=format)

    @RequireInstance
    def settings_badges_edit(self, id, part, badge_id, format='html'):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = settings_menu(c.page_instance, part)
        controller = self.badge_controller(c.page_instance, part)
        return controller.edit(badge_id, format=format)

    @RequireInstance
    def settings_badges_update(self, id, part, badge_id, format='html'):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = settings_menu(c.page_instance, part)
        controller = self.badge_controller(c.page_instance, part)
        return controller.update(badge_id, format=format)

    @RequireInstance
    def settings_badges_ask_delete(self, id, part, badge_id, format='html'):
        c.page_instance = self._get_current_instance(id)
        controller = self.badge_controller(c.page_instance, part)
        return controller.ask_delete(badge_id, format=format)

    @RequireInstance
    def settings_badges_delete(self, id, part, badge_id, format='html'):
        c.page_instance = self._get_current_instance(id)
        controller = self.badge_controller(c.page_instance, part)
        return controller.delete(badge_id, format=format)

    def _members_import_form(self, id):
        c.page_instance = self._get_current_instance(id)
        return render("/instance/members_import.html")

    @RequireInstance
    def members_import(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)
        return htmlfill.render(
            self._members_import_form(id),
            defaults={
                '_method': 'PUT',
                '_tok': csrf.token_id()})

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=UserImportForm(),
              form="_members_import_form",
              post_only=True, auto_error_formatter=error_formatter,
              state=get_user_import_state())
    def members_import_save(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        try:
            self.form_result = UserImportForm().to_python(
                request.params, state=get_user_import_state())
            require.instance.edit(c.page_instance)
            data = user_import(self.form_result['users_csv'],
                               self.form_result['email_subject'],
                               self.form_result['email_template'],
                               c.user,
                               c.instance)
            return render("/instance/members_import_success.html",
                          data, overlay=format == u'overlay')
        except formencode.Invalid as i:
            return self._members_import_form(errors=i.unpack_errors())

# --[ template ]------------------------------------------------------------

    def settings_sname_form(self, id):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = settings_menu(c.page_instance, 'sname')
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
              post_only=True, auto_error_formatter=error_formatter)
    def settings_sname_update(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)

        updated = update_attributes(c.page_instance, self.form_result, [])
        return self._settings_result(updated, c.page_instance, 'sname')

    def _presets_update(self, instance, form_result):
        active_settings = set()
        all_settings = set()
        for key, settings in PRESETS.iteritems():
            if form_result.get(key):
                active_settings.update(settings)
            all_settings.update(settings)

        updated = False
        for setting in active_settings:
            if not getattr(instance, setting):
                setattr(instance, setting, True)
                updated = True
        for setting in all_settings.difference(active_settings):
            if getattr(instance, setting):
                setattr(instance, setting, False)
                updated = True

        if updated:
            model.meta.Session.add(instance)
            model.meta.Session.commit()

        return updated

    def settings_presets_form(self, id):
        c.page_instance = self._get_current_instance(id)
        c.settings_menu = settings_menu(c.page_instance, 'presets')
        return render("/instance/settings_presets.html")

    @RequireInstance
    def settings_presets(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)
        return htmlfill.render(
            self.settings_presets_form(id),
            defaults={'_tok': csrf.token_id()})

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=InstancePresetsForm(),
              form="settings_presets_form",
              post_only=True, auto_error_formatter=error_formatter)
    def settings_presets_update(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)

        updated = self._presets_update(c.page_instance, self.form_result)
        return self._settings_result(updated, c.page_instance, 'presets')

    def presets_form(self, id):
        c.page_instance = self._get_current_instance(id)
        return render("/instance/presets.html")

    @RequireInstance
    def presets(self, id, format=u'html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)
        return formencode.htmlfill.render(
            self.presets_form(id),
            defaults={'_tok': csrf.token_id()})

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=InstancePresetsForm(), form="presets_form")
    def presets_update(self, id, format=u'html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)

        self._presets_update(c.page_instance, self.form_result)

        if config.get_bool('adhocracy.instance.show_settings_after_create'):
            member = 'settings/overview'
        else:
            member = None

        return ret_success(
            message=_(u'Instance created successfully. You can now configure '
                      u'it in greater detail if you wish.'),
            category='success', entity=c.page_instance,
            member=member)

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
                           c.page_instance.label,
                           force_path='/')

    @RequireInstance
    def ask_join(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.join(c.page_instance)
        return render('/instance/ask_join.html')

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
                               'instance': c.page_instance.label
                           },
                           category='success',
                           force_path=c.came_from)

    def ask_leave(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.leave(c.page_instance)

        c.tile = tiles.instance.InstanceTile(c.page_instance)
        return render('/instance/ask_leave.html')

    @csrf.RequireInternalRequest(methods=['POST'])
    def leave(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        if c.page_instance not in c.user.instances:
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
                update_entity(c.user, model.UPDATE)

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

    def get_region(self, id):
        c.instance = self._get_current_instance(id)

        if c.instance.region is None:
            feature = {}
        else:
            j = model.meta.Session.query(
                func.ST_AsGeoJSON(c.instance.region.boundary)).one()[0]
            instance_props = {
                'name': c.instance.region.name,
                'adminLevel': c.instance.region.admin_level,
                'adminType': c.instance.region.admin_type,
                'regionId': c.instance.region.id,
                'adminCenter': None
            }
            add_instance_props(c.instance, instance_props)

            feature = geojson.Feature(
                geometry=geojson.loads(j),
                properties=instance_props
            )

            admin_center_props = {
                'url': h.base_url(''),
                'label': c.instance.label
            }
            add_instance_props(c.instance, admin_center_props)
            feature.properties['adminCenter'] = geojson.Feature(
                geometry=get_instance_geo_centre(c.instance),
                properties=admin_center_props
            )

        return render_geojson(feature)

    @RequireInstance
    def get_proposal_geotags(self, id):
        c.instance = get_entity_or_abort(model.Instance, id)
        require.instance.show(c.instance)

        proposals = model.Proposal.\
            all_q(instance=c.instance).\
            filter(model.Proposal.geotag != None).\
            all()  # noqa

        features = geojson.FeatureCollection(
            [p.get_geojson_feature() for p in proposals])

        return render_geojson(features)

    @RequireInstance
    def get_page_geotags(self, id):
        c.instance = get_entity_or_abort(model.Instance, id)
        require.instance.show(c.instance)

        pages = model.Page.\
            all_q(instance=c.instance, functions=model.Page.LISTED).\
            filter(model.Page.geotag != None).\
            all()  # noqa

        features = geojson.FeatureCollection(
            [p.get_geojson_feature() for p in pages])

        return render_geojson(features)

    def get_all_instance_regions_json(self):
        require.instance.index()
        instances = model.Instance.all()

        def make_feature(instance):
            j = model.meta.Session.query(
                func.ST_AsGeoJSON(instance.region.boundary)).one()[0]
            geo_centre = get_instance_geo_centre(instance)
            admin_centre_feature = geojson.Feature(
                geometry=geo_centre,
                properties={
                    'url': h.base_url(instance=instance),
                    'label': instance.label,
                    'numProposals': instance.num_proposals,
                    'numMembers': instance.num_members,
                })
            feature = geojson.Feature(
                geometry=geojson.loads(j),
                properties={
                    'url': h.base_url(instance=instance),
                    'label': instance.label,
                    'admin_center': admin_centre_feature
                })
            return feature

        features = geojson.FeatureCollection(
            [make_feature(i) for i in instances if i.region is not None])
        return render_geojson(features)

    def get_all_instance_centres_json(self):

        # TODO: Cache invaldation
        @cache.memoize('geo_all_instance_centres')
        def calculate():

            require.instance.index()
            instances = model.Instance.all()

            def make_feature(instance):
                geo_centre = get_instance_geo_centre(instance)
                if config.get_bool('adhocracy.geo.use_instancebadge_colors')\
                   and instance.instancebadges:
                    # Naively assume that only one badge is set
                    color = instance.instancebadges[0].badge.color
                else:
                    color = None
                feature = geojson.Feature(
                    id=instance.id,
                    geometry=geo_centre,
                    properties={
                        'url': h.base_url(instance=instance),
                        'label': instance.label,
                        'isAuthenticated': instance.is_authenticated,
                        'color': color,
                    })
                add_instance_props(instance, feature.properties)
                return feature

            return render_geojson(geojson.FeatureCollection(
                [make_feature(i) for i in instances if i.region is not None]),
                set_mime=False)

        set_json_response()
        return calculate()
