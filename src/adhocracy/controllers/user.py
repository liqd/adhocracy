from collections import OrderedDict
import logging
import re
import urllib

import formencode
from formencode import ForEach, htmlfill, validators

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort
from pylons.controllers.util import redirect
from pylons.decorators import validate
from pylons.i18n import _
from pylons.i18n import lazy_ugettext as L_

from webob.exc import HTTPFound

from repoze.who.api import get_api

from adhocracy import config
from adhocracy import forms, model
from adhocracy import i18n
from adhocracy.lib import democracy, event, helpers as h, pager
from adhocracy.lib import sorting, search as libsearch, tiles, text
from adhocracy.lib.auth import require, login_user, guard
from adhocracy.lib.auth.authorization import has
from adhocracy.lib.auth.csrf import RequireInternalRequest, token_id
from adhocracy.lib.auth.welcome import (welcome_enabled, can_welcome,
                                        welcome_url)
from adhocracy.lib.base import BaseController
from adhocracy.lib.instance import RequireInstance
import adhocracy.lib.mail as libmail
from adhocracy.lib.pager import (NamedPager, solr_global_users_pager,
                                 solr_instance_users_pager, PROPOSAL_SORTS)
from adhocracy.lib.settings import INSTANCE_UPDATED_MSG
from adhocracy.lib.settings import NO_UPDATE_REQUIRED
from adhocracy.lib.settings import error_formatter
from adhocracy.lib.settings import Menu
from adhocracy.lib.settings import settings_url
from adhocracy.lib.settings import update_attributes
from adhocracy.lib.staticpage import add_static_content
from adhocracy.lib.templating import render, render_json, ret_abort
from adhocracy.lib.templating import ret_success
from adhocracy.lib.queue import update_entity
from adhocracy.lib.util import get_entity_or_abort, random_token


log = logging.getLogger(__name__)


def settings_menu(instance, current):

    show_login = (h.user.can_change_password(c.page_user) or
                  'openid' in h.allowed_login_types())
    show_optional = bool(config.get('adhocracy.user.optional_attributes'))

    return Menu.create(instance, current, OrderedDict([
        ('personal', (L_(u'Personal'), True, 'settings')),
        ('login', (L_(u'Login'), show_login)),
        ('notifications', (L_('Notifications'),)),
        ('advanced', (L_('Advanced'),)),
        ('optional', (L_('Optional'), show_optional)),
    ]))


class UserCreateForm(formencode.Schema):
    allow_extra_fields = True
    if not config.get_bool('adhocracy.force_randomized_user_names'):
        user_name = formencode.All(validators.PlainText(not_empty=True),
                                   forms.UniqueUsername(),
                                   forms.ContainsChar())
    if config.get_bool('adhocracy.set_display_name_on_register'):
        display_name = validators.String(not_empty=False, if_missing=None)
    email = formencode.All(validators.Email(
        not_empty=config.get_bool('adhocracy.require_email')),
        forms.UniqueOtherEmail())
    password = validators.String(not_empty=True)
    password_confirm = validators.String(not_empty=True)
    chained_validators = [validators.FieldsMatch(
        'password', 'password_confirm')]


class UserSettingsPersonalForm(formencode.Schema):
    allow_extra_fields = True
    locale = forms.ValidLocale()
    display_name = validators.String(not_empty=False)
    bio = validators.String(max=1000, min=0, not_empty=False)


class UserSettingsLoginForm(formencode.Schema):
    allow_extra_fields = True
    password_change = validators.String(not_empty=False, if_missing=None)
    password_confirm = validators.String(not_empty=False, if_missing=None)
    chained_validators = [validators.FieldsMatch(
        'password_change', 'password_confirm')]


class UserSettingsNotificationsForm(formencode.Schema):
    allow_extra_fields = True
    email = formencode.All(validators.Email(
        not_empty=config.get_bool('adhocracy.require_email')),
        forms.UniqueOtherEmail())
    email_priority = validators.Int(min=0, max=6, not_empty=False,
                                    if_missing=3)
    email_messages = validators.StringBool(not_empty=False, if_empty=False,
                                           if_missing=False)


class UserSettingsAdvancedForm(formencode.Schema):
    allow_extra_fields = True
    no_help = validators.StringBool(not_empty=False, if_empty=False,
                                    if_missing=False)
    page_size = validators.Int(min=1, max=200, not_empty=False,
                               if_empty=10, if_missing=10)
    proposal_sort_order = forms.ProposalSortOrder()


class UserSettingsOptionalForm(formencode.Schema):
    allow_extra_fields = True
    chained_validators = [
        forms.common.OptionalAttributes(),
    ]


class UserCodeForm(formencode.Schema):
    allow_extra_fields = True
    c = validators.String(not_empty=False)


class UserResetApplyForm(formencode.Schema):
    allow_extra_fields = True
    email = validators.Email(not_empty=True)


class UserGroupmodForm(formencode.Schema):
    allow_extra_fields = True
    to_group = forms.ValidInstanceGroup()


class UserFilterForm(formencode.Schema):
    allow_extra_fields = True
    users_q = validators.String(max=255, not_empty=False, if_empty=u'',
                                if_missing=u'')
    users_group = validators.String(max=255, not_empty=False, if_empty=None,
                                    if_missing=None)


class UserBadgesForm(formencode.Schema):
    allow_extra_fields = True
    badge = ForEach(forms.ValidUserBadge())


class UserSetPasswordForm(formencode.Schema):
    allow_extra_fields = True
    password = validators.String(not_empty=False)


class NoPasswordForm(formencode.Schema):
    allow_extra_fields = True
    login = validators.String(not_empty=False)


class UserController(BaseController):

    def __init__(self):
        super(UserController, self).__init__()
        c.active_subheader_nav = 'members'

    @RequireInstance
    @guard.user.index()
    @validate(schema=UserFilterForm(), post_only=False, on_get=True)
    def index(self, format='html'):

        default_sorting = config.get(
            'adhocracy.listings.instance_user.sorting', 'ACTIVITY')
        c.users_pager = solr_instance_users_pager(c.instance, default_sorting)

        #if format == 'json':
        ##    return render_json(c.users_pager)

        c.tutorial_intro = _('tutorial_user_index_intro')
        c.tutorial = 'user_index'
        return render("/user/index.html")

    @guard.perm('user.index_all')
    def all(self):
        c.users_pager = solr_global_users_pager()
        return render("/user/all.html")

    def new(self, defaults=None):
        if not h.allow_user_registration():
            return ret_abort(
                _("Sorry, registration has been disabled by administrator."),
                category='error', code=403)
        c.active_global_nav = "login"
        if c.user:
            redirect('/')
        else:
            data = {}
            captcha_enabled = config.get('recaptcha.public_key', "")
            data['recaptcha'] = captcha_enabled and h.recaptcha.displayhtml(
                use_ssl=True)
            if defaults is None:
                defaults = {}
            defaults['_tok'] = token_id()
            add_static_content(data, u'adhocracy.static_agree_text',
                               body_key=u'agree_text', title_key='_ignored')
            return htmlfill.render(render("/user/register.html", data),
                                   defaults=defaults)

    @RequireInternalRequest(methods=['POST'])
    @guard.user.create()
    @validate(schema=UserCreateForm(), form="new", post_only=True)
    def create(self):
        if not h.allow_user_registration():
            return ret_abort(
                _("Sorry, registration has been disabled by administrator."),
                category='error', code=403)

        if self.email_is_blacklisted(self.form_result['email']):
            return ret_abort(_("Sorry, but we don't accept registrations with "
                               "this email address."), category='error',
                             code=403)

        # SPAM protection recaptcha
        captcha_enabled = config.get('recaptcha.public_key', "")
        if captcha_enabled:
            recaptcha_response = h.recaptcha.submit()
            if not recaptcha_response.is_valid:
                c.recaptcha = h.recaptcha.displayhtml(
                    use_ssl=True,
                    error=recaptcha_response.error_code)
                redirect("/register")
        # SPAM protection hidden input
        input_css = self.form_result.get("input_css")
        input_js = self.form_result.get("input_js")
        if input_css or input_js:
            redirect("/")

        #create user
        if config.get_bool('adhocracy.force_randomized_user_names'):
            user_name = None
        else:
            user_name = self.form_result.get("user_name")
        user = model.User.create(
            user_name,
            self.form_result.get("email"),
            password=self.form_result.get("password"),
            locale=c.locale,
            display_name=self.form_result.get("display_name"))
        model.meta.Session.commit()

        event.emit(event.T_USER_CREATE, user)
        libmail.send_activation_link(user)

        if c.instance:
            membership = user.instance_membership(c.instance)
            if membership is None:
                membership = model.Membership(user, c.instance,
                                              c.instance.default_group)
                model.meta.Session.expunge(membership)
                model.meta.Session.add(membership)
                model.meta.Session.commit()

        # authenticate the new registered member using the repoze.who
        # api. This is done here and not with an redirect to the login
        # to omit the generic welcome message
        who_api = get_api(request.environ)
        login_configuration = h.allowed_login_types()
        if 'username+password' in login_configuration:
            login = user.user_name
        elif 'email+password' in login_configuration:
            login = self.form_result.get("email")
        else:
            raise Exception('We have no way of authenticating the newly'
                            'created user %s; check adhocracy.login_type' %
                            login)
        credentials = {
            'login': login,
            'password': self.form_result.get("password")
        }
        authenticated, headers = who_api.login(credentials)
        if authenticated:
            session['logged_in'] = True
            session.save()
            came_from = request.params.get('came_from')
            if came_from:
                location = urllib.unquote_plus(came_from)
            else:
                location = h.user.post_register_url(user)
            raise HTTPFound(location=location, headers=headers)
        else:
            raise Exception('We have added the user to the Database '
                            'but cannot authenticate him: '
                            '%s (%s)' % (credentials['login'], user))

    def edit(self, id):
        """ legacy url """
        redirect(h.entity_url(c.user, instance=c.instance, member='settings'))

    def _settings_result(self, updated, user, setting_name, message=None):
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
        *user* (:class:`adhocracy.model.User`)
           The user to generate the redirect URL for.
        *setting_name* (str)
           The setting name for which the URL will be build.
        *message* (unicode)
           An explicit message to use instead of the generic message.

        Returns
           The message generated or given.
        '''
        if updated:
            event.emit(event.T_USER_EDIT, c.user)
            message = message if message else unicode(INSTANCE_UPDATED_MSG)
            category = 'success'
        else:
            message = message if message else unicode(NO_UPDATE_REQUIRED)
            category = 'notice'
        h.flash(message, category=category)
        response.status_int = 303
        url = settings_menu(user, setting_name).url_for(setting_name)
        response.headers['location'] = url
        return unicode(message)

    def _settings_all(self, id):
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        require.user.edit(c.page_user)
        if c.instance is None:
            c.active_global_nav = 'user'

    def _settings_personal_form(self, id):
        self._settings_all(id)
        c.settings_menu = settings_menu(c.page_user, 'personal')

        c.locales = []
        for locale in i18n.LOCALES:
            c.locales.append({'value': str(locale),
                              'label': locale.display_name,
                              'selected': locale == c.user.locale})

        c.salutations = [
            {'value': u'u', 'label': _(u'Gender-neutral')},
            {'value': u'f', 'label': _(u'Female')},
            {'value': u'm', 'label': _(u'Male')},
        ]

        return render("/user/settings_personal.html")

    def settings_personal(self, id):
        form_content = self._settings_personal_form(id)
        return htmlfill.render(
            form_content,
            defaults={
                '_method': 'PUT',
                'display_name': c.page_user.display_name,
                'locale': c.page_user.locale,
                'bio': c.page_user.bio,
                'gender': c.page_user.gender,
                '_tok': token_id()})

    @validate(schema=UserSettingsPersonalForm(),
              form="_settings_personal_form",
              post_only=True, auto_error_formatter=error_formatter)
    def settings_personal_update(self, id):
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        require.user.edit(c.page_user)
        updated = update_attributes(c.page_user, self.form_result,
                                    ['display_name', 'locale', 'bio'])

        if config.get_bool('adhocracy.enable_gender'):
            gender = self.form_result.get("gender")
            if gender in ('f', 'm', 'u') and gender != c.page_user.gender:
                c.page_user.gender = gender
                updated = True
                model.meta.Session.commit()

        return self._settings_result(updated, c.page_user, 'personal')

    def _settings_login_form(self, id):
        self._settings_all(id)
        c.settings_menu = settings_menu(c.page_user, 'login')
        c.locales = []
        for locale in i18n.LOCALES:
            c.locales.append({'value': str(locale),
                              'label': locale.display_name,
                              'selected': locale == c.user.locale})

        return render("/user/settings_login.html")

    def settings_login(self, id):
        form_content = self._settings_login_form(id)
        return htmlfill.render(
            form_content,
            defaults={
                '_method': 'PUT',
            })

    @validate(schema=UserSettingsLoginForm(), form="_settings_login_form",
              post_only=True, auto_error_formatter=error_formatter)
    def settings_login_update(self, id):
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        require.user.edit(c.page_user)

        updated = False
        if self.form_result.get("password_change"):
            if h.user.can_change_password(c.page_user):
                c.page_user.password = self.form_result.get("password_change")
                updated = True
            else:
                log.error(
                    'Attempt to change password although disabled (user %s)' %
                    c.page_user.user_name)

        return self._settings_result(updated, c.page_user, 'login')

    def _settings_notifications_form(self, id):
        self._settings_all(id)
        c.settings_menu = settings_menu(c.page_user, 'notifications')

        c.locales = []
        for locale in i18n.LOCALES:
            c.locales.append({'value': str(locale),
                              'label': locale.display_name,
                              'selected': locale == c.user.locale})

        return render("/user/settings_notifications.html")

    def settings_notifications(self, id):
        form_content = self._settings_notifications_form(id)
        return htmlfill.render(
            form_content,
            defaults={
                '_method': 'PUT',
                'email': c.page_user.email,
                'email_priority': c.page_user.email_priority,
                'email_messages': c.page_user.email_messages,
                '_tok': token_id()})

    @validate(schema=UserSettingsNotificationsForm(),
              form="_settings_notifications_form",
              post_only=True, auto_error_formatter=error_formatter)
    def settings_notifications_update(self, id):
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        require.user.edit(c.page_user)
        old_email = c.page_user.email
        old_activated = c.page_user.is_email_activated()
        updated = update_attributes(c.page_user, self.form_result,
                                    ['email',
                                     'email_priority',
                                     'email_messages'])
        model.meta.Session.commit()

        email = self.form_result.get("email")
        if email != old_email:
            # Logging email address changes in order to ensure accountability
            log.info('User %s changed email address from %s%s to %s' % (
                c.page_user.user_name,
                old_email,
                ' (validated)' if old_activated else '',
                email))
            libmail.send_activation_link(c.page_user)
        c.page_user.email = email
        c.page_user.email_priority = self.form_result.get("email_priority")
        #if c.page_user.twitter:
        #    c.page_user.twitter.priority = \
        #        self.form_result.get("twitter_priority")
        #    model.meta.Session.add(c.page_user.twitter)
        return self._settings_result(updated, c.page_user, 'notifications')

    def _settings_advanced_form(self, id):
        self._settings_all(id)
        c.tile = tiles.user.UserTile(c.page_user)
        c.settings_menu = settings_menu(c.page_user, 'advanced')

        c.pager_sizes = [{'value': str(size),
                          'label': str(size),
                          'selected': size == c.user.page_size}
                         for size in [10, 20, 50, 100, 200]]
        c.sorting_orders = PROPOSAL_SORTS

        return render("/user/settings_advanced.html")

    def settings_advanced(self, id):
        form_content = self._settings_advanced_form(id)
        return htmlfill.render(
            form_content,
            defaults={
                '_method': 'PUT',
                'no_help': c.page_user.no_help,
                'page_size': c.page_user.page_size,
                'proposal_sort_order': c.page_user.proposal_sort_order,
                '_tok': token_id()})

    @validate(schema=UserSettingsAdvancedForm(),
              form="_settings_advanced_form",
              post_only=True, auto_error_formatter=error_formatter)
    def settings_advanced_update(self, id):
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        require.user.edit(c.page_user)
        updated = update_attributes(c.page_user, self.form_result,
                                    ['no_help',
                                     'page_size',
                                     'proposal_sort_order'])

        return self._settings_result(updated, c.page_user, 'advanced')

    def _settings_optional_form(self, id, data={}):
        if not config.get('adhocracy.user.optional_attributes'):
            abort(400, _("No optional attributes defined."))
        self._settings_all(id)
        data['page_user'] = c.page_user
        data['tile'] = tiles.user.UserTile(c.page_user)
        data['settings_menu'] = settings_menu(c.page_user, 'optional')

        data['optional_attributes'] = config.get_optional_user_attributes()
        add_static_content(data,
                           u'adhocracy.static_optional_path')

        return render("/user/settings_optional.html", data)

    def settings_optional(self, id):
        form_content = self._settings_optional_form(id)
        defaults = c.page_user.optional_attributes or {}

        # Workaround, as htmlfill will match select option values in their
        # html encoded form.
        # Proper fix would be to explicitly declare database and shown option
        # value in the configuration in adhocracy.user.optional_attributes.xxx
        # That way the shown value can also be changed later.
        import cgi
        defaults = dict((k, cgi.escape(unicode(v)))
                        for k, v in defaults.items())

        defaults.update({
            '_method': 'PUT',
            '_tok': token_id()})
        return htmlfill.render(form_content, defaults=defaults)

    @validate(schema=UserSettingsOptionalForm(),
              form="_settings_optional_form",
              post_only=True, auto_error_formatter=error_formatter)
    def settings_optional_update(self, id):
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        require.user.edit(c.page_user)
        updated = self._update_optional_attributes(c.page_user,
                                                   self.form_result)
        if updated:
            model.meta.Session.commit()

        return self._settings_result(updated, c.page_user, 'optional')

    def _update_optional_attributes(self, user, attributes):

        current = user.optional_attributes or {}
        updated = False
        for (key, _, _, _, _) in config.get_optional_user_attributes():
            if current.get(key, None) != attributes[key]:
                current[key] = attributes[key]
                updated = True
        if updated:
            user.optional_attributes = current
        return updated

    def redirect_settings(self, item=None):
        if c.user is None:
            redirect(h.login_redirect_url())
        if item is None:
            redirect(settings_url(c.user, None, force_url='settings'))
        else:
            redirect(settings_url(c.user, item))

    def redirect_settings_login(self):
        self.redirect_settings('login')

    def redirect_settings_notifications(self):
        self.redirect_settings('notifications')

    def redirect_settings_advanced(self):
        self.redirect_settings('advanced')

    def redirect_settings_optional(self):
        self.redirect_settings('optional')

    @RequireInternalRequest(methods=['POST'])
    @validate(schema=UserSetPasswordForm(), form='edit', post_only=True)
    def set_password(self, id):
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        require.user.edit(c.page_user)
        c.page_user.password = self.form_result.get('password')
        model.meta.Session.add(c.page_user)
        model.meta.Session.commit()

        h.flash(_('Password has been set. Have fun!'), 'success')
        redirect(h.base_url('/'))

    def reset_form(self):
        return render("/user/reset_form.html")

    @RequireInternalRequest(methods=['POST'])
    @validate(schema=UserResetApplyForm(), form="reset_form", post_only=True)
    def reset_request(self):
        user = model.User.find_by_email(self.form_result.get('email'))
        if user is None:
            msg = _("There is no user registered with that email address.")
            return htmlfill.render(self.reset_form(), errors=dict(email=msg))
        return self._handle_reset(user)

    def _handle_reset(self, user):
        c.page_user = user

        if welcome_enabled():
            welcome_code = (c.page_user.welcome_code
                            if c.page_user.welcome_code
                            else random_token())
            c.page_user.reset_code = u'welcome!' + welcome_code
            model.meta.Session.add(c.page_user)
            model.meta.Session.commit()
            url = welcome_url(c.page_user, welcome_code)
            body = (
                _("you have requested that your password be reset. In order "
                  "to confirm the validity of your claim, please open the "
                  "link below in your browser:") +
                "\n\n  " + url + "\n")
            libmail.to_user(c.page_user,
                            _("Login for %s") % h.site.name(),
                            body)
        else:
            c.page_user.reset_code = random_token()
            model.meta.Session.add(c.page_user)
            model.meta.Session.commit()
            url = h.base_url("/user/%s/reset?c=%s" % (c.page_user.user_name,
                                                      c.page_user.reset_code),
                             absolute=True)
            body = (
                _("you have requested that your password be reset. In order "
                  "to confirm the validity of your claim, please open the "
                  "link below in your browser:") +
                "\r\n\r\n  " + url + "\n" +
                _("Your user name to login is: %s") % c.page_user.user_name)

            libmail.to_user(c.page_user, _("Reset your password"), body)
        return render("/user/reset_pending.html")

    @validate(schema=UserCodeForm(), form="reset_form", post_only=False,
              on_get=True)
    def reset(self, id):
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        try:
            if c.page_user.reset_code != self.form_result.get('c'):
                raise ValueError()
            new_password = random_token()
            c.page_user.password = new_password
            model.meta.Session.add(c.page_user)
            model.meta.Session.commit()
            body = (
                _("your password has been reset. It is now:") +
                "\r\n\r\n  " + new_password + "\r\n\r\n" +
                _("Please login and change the password in your user "
                  "settings.") + "\n\n" +
                _("Your user name to login is: %s") % c.page_user.user_name
            )
            libmail.to_user(c.page_user, _("Your new password"), body)
            h.flash(_("Success. You have been sent an email with your new "
                      "password."), 'success')
        except Exception:
            h.flash(_("The reset code is invalid. Please repeat the password"
                      " recovery procedure."), 'error')
        redirect('/login')

    @validate(schema=UserCodeForm(), form="edit", post_only=False, on_get=True)
    def activate(self, id):
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        code = self.form_result.get('c')

        if c.page_user.activation_code != code:
            h.flash(_("The activation code is invalid. Please have it "
                      "resent."), 'error')
            redirect(h.entity_url(c.page_user))
        if c.page_user.activation_code is None:
            h.flash(_(u'Thank you, The address is already activated.'))
            redirect(h.entity_url(c.page_user))

        c.page_user.activation_code = None
        model.meta.Session.commit()
        if code.startswith(model.User.IMPORT_MARKER):
            # Users imported by admins
            login_user(c.page_user, request, response)
            h.flash(_("Welcome to %s") % h.site.name(), 'success')
            if c.instance:
                membership = model.Membership(c.page_user, c.instance,
                                              c.instance.default_group)
                model.meta.Session.expunge(membership)
                model.meta.Session.add(membership)
                model.meta.Session.commit()
                redirect(h.entity_url(c.instance))
            else:
                redirect(h.base_url('/instance', None))
        else:
            h.flash(_("Your email has been confirmed."), 'success')
            redirect(h.entity_url(c.page_user))

        redirect(h.entity_url(c.page_user))

    @RequireInternalRequest()
    def resend(self, id):
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        require.user.edit(c.page_user)
        libmail.send_activation_link(c.page_user)
        path = request.params.get('came_from', None)
        ret_success(
            message=_("The activation link has been re-sent to your email "
                      "address."), category='success',
            entity=c.page_user, member='settings/notifications',
            format=None, force_path=path)

    def show(self, id, format='html'):
        if c.instance is None:
            c.active_global_nav = 'user'
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        require.user.show(c.page_user)

        if format == 'json':
            return render_json(c.page_user)

        query = model.meta.Session.query(model.Event)
        query = query.filter(model.Event.user == c.page_user)
        query = query.order_by(model.Event.time.desc())
        query = query.limit(10)
        if format == 'rss':
            query = query.limit(50)
            return event.rss_feed(
                query.all(), "%s Latest Actions" % c.page_user.name,
                h.base_url('/user/%s' % c.page_user.user_name, None),
                c.page_user.bio)
        c.events_pager = pager.events(query.all())
        c.tile = tiles.user.UserTile(c.page_user)
        self._common_metadata(c.page_user, add_canonical=True)
        return render("/user/show.html")

    def login(self):
        c.active_global_nav = "login"
        if c.user:
            redirect('/')
        else:
            return self._render_loginform()

    def _render_loginform(self, errors=None, defaults=None):
        if defaults is None:
            defaults = dict(request.params)
            defaults.setdefault('have_password', 'true')
            if '_login_value' in request.environ:
                defaults['login'] = request.environ['_login_value']
            defaults['_tok'] = token_id()
        data = {}
        data['hide_locallogin'] = (
            config.get_bool('adhocracy.hide_locallogin')
            and not 'locallogin' in request.GET)
        add_static_content(data, u'adhocracy.static_login_path')
        form = render('/user/login_tile.html', data)
        form = htmlfill.render(form,
                               errors=errors,
                               defaults=defaults)
        return render('/user/login.html', {'login_form_code': form})

    def perform_login(self):
        pass  # managed by repoze.who

    def post_login(self):
        if c.user:
            session['logged_in'] = True
            session.save()
            came_from = request.params.get('came_from', None)
            if came_from is not None:
                redirect(urllib.unquote_plus(came_from))
            # redirect to the dashboard inside the instance exceptionally
            # to be able to link to proposals and norms in the welcome
            # message.
            redirect(h.user.post_login_url(c.user))
        else:
            login_configuration = h.allowed_login_types()
            error_message = _("Invalid login")

            if 'username+password' in login_configuration:
                if 'email+password' in login_configuration:
                    error_message = _("Invalid email / user name or password")
                else:
                    error_message = _("Invalid user name or password")
            else:
                if 'email+password' in login_configuration:
                    error_message = _("Invalid email or password")

            return self._render_loginform(errors={"login": error_message})

    def logout(self):
        pass  # managed by repoze.who

    def post_logout(self):
        login_type = session.get('login_type', None)
        session.delete()
        # Note: This flash message only works with adhocracy cookie sessions
        # and not with beaker sessions due to the way session deletion is
        # handled in beaker.
        if login_type == 'shibboleth':
            logout_url = config.get('adhocracy.shibboleth_logout_url', None)
            if logout_url is None:
                target_msg = u''
            else:
                target_msg = (_(u"You can finish that session <a href='%s'>"
                                u"here</a>.") % logout_url)
            h.flash(_(
                u"<p>You have successfully logged out of Adhocracy. However "
                u"you might still be logged in at the central identity "
                u"provider. %s</p>"
                u""
                u"<p>If you're on a public computer, please close your "
                u"browser to complete the logout.</p>") % target_msg,
                'warning')
        elif login_type == 'openid':
            h.flash(_(
                u"You have successfully logged out of Adhocracy. However you "
                u"might still be logged in through your OpenID provider. "),
                'warning')
        else:
            h.flash(_(u"Successfully logged out"), 'success')
        redirect(h.base_url())

    @RequireInternalRequest(methods=['POST'])
    @validate(schema=NoPasswordForm(), post_only=True)
    def nopassword(self):
        """ (Alternate login) User clicked "I have no password" """

        assert config.get('adhocracy.login_style') == 'alternate'
        user = request.environ['_adhocracy_nopassword_user']
        if user:
            return self._handle_reset(user)

        login = self.form_result.get('login')
        if u'@' not in login:
            msg = _("Please use a valid email address.")
            return self._render_loginform(errors={'login': msg})

        if h.allow_user_registration():
            handle = login.partition(u'@')[0]
            defaults = {
                'email': login,
                'user_name': re.sub('[^0-9a-zA-Z_-]', '', handle),
            }
            return self.new(defaults=defaults)

        support_email = config.get('adhocracy.registration_support_email')
        if support_email:
            body = (_('A user tried to register on %s with the email address'
                      ' %s. Please contact them at %s .') %
                    (h.site.name(),
                     login,
                     h.base_url('/', absolute=True)))
            libmail.to_mail(
                to_name=h.site.name(),
                to_email=support_email,
                subject=_('Registration attempt on %s') % h.site.name(),
                body=body,
                decorate_body=False,
            )
            data = {
                'email': login,
            }
            return render('/user/registration_request_sent.html', data=data)

        return ret_abort(
            _("Sorry, registration has been disabled by administrator."),
            category='error', code=403)

    def dashboard(self, id):
        '''Render a personalized dashboard for users'''

        if 'logged_in' in session:
            c.fresh_logged_in = True
            c.suppress_attention_getter = True
            del session['logged_in']
            came_from = request.params.get('came_from')
            if came_from:
                c.came_from = came_from

        #user object
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        require.user.show_dashboard(c.page_user)
        #instances
        instances = c.page_user.instances
        #proposals
        proposals = [model.Proposal.all(instance=i) for i in instances]
        proposals = proposals and reduce(lambda x, y: x + y, proposals)
        c.proposals = proposals
        c.proposals_pager = pager.proposals(proposals, size=4,
                                            default_sort=sorting.entity_newest,
                                            enable_pages=False,
                                            enable_sorts=False)
        #polls
        polls = [p.adopt_poll for p in proposals if p.is_adopt_polling()]
        polls = filter(lambda p: not p.has_ended() and not p.is_deleted(),
                       polls)
        c.polls = polls
        c.polls_pager = pager.polls(polls,
                                    size=20,
                                    default_sort=sorting.entity_newest,
                                    enable_pages=False,
                                    enable_sorts=False,)
        #pages
        c.show_pages = any(instance.use_norms for instance in instances)
        if c.show_pages:
            require.page.index()
            pages = [model.Page.all(instance=i, functions=model.Page.LISTED)
                     for i in instances]
            pages = pages and reduce(lambda x, y: x + y, pages)
            c.pages = pages
            c.pages_pager = pager.pages(pages, size=3,
                                        default_sort=sorting.entity_newest,
                                        enable_pages=False,
                                        enable_sorts=False)
        #watchlist
        require.watch.index()
        c.active_global_nav = 'user'
        watches = model.Watch.all_by_user(c.page_user)
        entities = [w.entity for w in watches if (w.entity is not None)
                    and (not isinstance(w.entity, unicode))]
        c.watchlist_pager = NamedPager(
            'watches', entities,
            tiles.dispatch_row_with_comments,
            size=3,
            enable_pages=False,
            enable_sorts=False,
            default_sort=sorting.entity_newest)

        #render result
        c.tutorial = 'user_dashboard'
        c.tutorial_intro = _('tutorial_dashboard_title')
        return render('/user/dashboard.html')

    def dashboard_proposals(self, id):
        '''Render all proposals for all instances the user is member'''
        #user object
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        require.user.show(c.page_user)
        #instances
        instances = c.page_user.instances
        #proposals
        proposals = [model.Proposal.all(instance=i) for i in instances]
        proposals = proposals and reduce(lambda x, y: x + y, proposals)
        c.proposals_pager = pager.proposals(proposals)
        #render result
        return render("/user/proposals.html")

    def dashboard_pages(self, id):
        '''Render all proposals for all instances the user is member'''
        #user object
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        require.user.show(c.page_user)
        #instances
        instances = c.page_user.instances
        #pages
        require.page.index()
        pages = [model.Page.all(instance=i, functions=model.Page.LISTED)
                 for i in instances]
        pages = pages and reduce(lambda x, y: x + y, pages)
        c.pages_pager = pager.pages(pages)
        #render result
        return render("/user/pages.html")

    @guard.perm("user.view")
    def complete(self):
        prefix = unicode(request.params.get('q', u''))
        users = model.User.complete(prefix, 15)
        results = []
        for user in users:
            if user == c.user:
                continue
            display = "%s (%s)" % (user.user_name, user.name) if \
                      user.display_name else user.name
            results.append(dict(display=display, user=user.user_name))
        return render_json(results)

    @RequireInstance
    def votes(self, id, format='html'):
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        require.user.show(c.page_user)
        decisions = democracy.Decision.for_user(c.page_user, c.instance)

        if format == 'json':
            return render_json(list(decisions))

        decisions = filter(lambda d: d.poll.action != model.Poll.RATE,
                           decisions)
        c.decisions_pager = pager.user_decisions(decisions)
        self._common_metadata(c.page_user, member='votes')
        return render("/user/votes.html")

    @RequireInstance
    def delegations(self, id, format='html'):
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        require.user.show(c.page_user)
        scope_id = request.params.get('scope', None)

        if format == 'json':
            delegations = model.Delegation.find_by_principal(c.page_user)
            scope = model.Delegateable.find(scope_id) if scope_id else None
            if scope is not None:
                delegations = [d for d in delegations if d.is_match(scope)]
            delegations_pager = pager.delegations(delegations)
            return render_json(delegations_pager)

        c.dgbs = []
        if scope_id:
            c.scope = forms.ValidDelegateable().to_python(scope_id)
            c.dgbs = [c.scope] + c.scope.children
        else:
            c.dgbs = model.Delegateable.all(instance=c.instance)
        c.nodeClass = democracy.DelegationNode
        self._common_metadata(c.page_user, member='delegations')
        return render("/user/delegations.html")

    def instances(self, id, format='html'):
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        require.user.show(c.page_user)
        instances = [i for i in c.page_user.instances if i.is_shown()]
        c.instances_pager = pager.instances(instances)

        if format == 'json':
            return render_json(c.instances_pager)

        self._common_metadata(c.page_user, member='instances',
                              add_canonical=True)
        return render("/user/instances.html")

    @guard.watch.index()
    def watchlist(self, id, format='html'):
        c.active_global_nav = 'watchlist'
        c.page_user = get_entity_or_abort(model.User, id,
                                          instance_filter=False)
        require.user.show_watchlist(c.page_user)
        watches = model.Watch.all_by_user(c.page_user)
        entities = [w.entity for w in watches if (w.entity is not None)
                    and (not isinstance(w.entity, unicode))]

        c.entities_pager = NamedPager(
            'watches', entities, tiles.dispatch_row_with_comments,
            sorts={_("oldest"): sorting.entity_oldest,
                   _("newest"): sorting.entity_newest},
            default_sort=sorting.entity_newest)

        if format == 'json':
            return render_json(c.entities_pager)

        self._common_metadata(c.page_user, member='watchlist')
        return render("/user/watchlist.html")

    @RequireInstance
    @RequireInternalRequest()
    @validate(schema=UserGroupmodForm(), form="edit",
              post_only=False, on_get=True)
    def groupmod(self, id):
        c.page_user = get_entity_or_abort(model.User, id)
        require.user.supervise(c.page_user)
        to_group = self.form_result.get("to_group")
        had_vote = c.page_user._has_permission("vote.cast")
        for membership in c.page_user.memberships:
            if (not membership.is_expired() and
                    membership.instance == c.instance):
                membership.group = to_group
        model.meta.Session.commit()
        event.emit(event.T_INSTANCE_MEMBERSHIP_UPDATE, c.page_user,
                   instance=c.instance, group=to_group, admin=c.user)
        if had_vote and not c.page_user._has_permission("vote.cast"):
            # user has lost voting privileges
            c.page_user.revoke_delegations(c.instance)
        model.meta.Session.commit()
        redirect(h.entity_url(c.page_user))

    @RequireInstance
    @RequireInternalRequest()
    def ban(self, id):
        c.page_user = get_entity_or_abort(model.User, id)
        require.user.manage(c.page_user)
        c.page_user.banned = True
        model.meta.Session.commit()
        h.flash(_("The account has been suspended."), 'success')
        redirect(h.entity_url(c.page_user))

    @RequireInstance
    @RequireInternalRequest()
    def unban(self, id):
        c.page_user = get_entity_or_abort(model.User, id)
        require.user.manage(c.page_user)
        c.page_user.banned = False
        model.meta.Session.commit()
        h.flash(_("The account has been re-activated."), 'success')
        redirect(h.entity_url(c.page_user))

    def ask_delete(self, id):
        c.page_user = get_entity_or_abort(model.User, id)
        require.user.delete(c.page_user)
        return render('/user/ask_delete.html')

    @RequireInternalRequest()
    def delete(self, id):
        c.page_user = get_entity_or_abort(model.User, id)
        require.user.delete(c.page_user)
        c.page_user.delete()
        model.meta.Session.commit()
        h.flash(_("The account has been deleted."), 'success')
        if c.instance is not None:
            redirect(h.instance.url(c.instance))
        else:
            redirect(h.site.base_url(instance=None))

    @guard.user.index()
    @validate(schema=UserFilterForm(), post_only=False, on_get=True)
    def filter(self):
        query = self.form_result.get('users_q')
        users = libsearch.query.run(query + u"*", entity_type=model.User,
                                    instance_filter=True)
        c.users_pager = pager.users(users, has_query=True)
        return c.users_pager.here()

    @guard.perm('instance.admin')
    def badges(self, id, errors=None):
        if has('global.admin'):
            c.badges = model.UserBadge.all(instance=None)
        else:
            c.badges = None
        c.page_user = get_entity_or_abort(model.User, id)
        instances = c.page_user and c.page_user.instances or []
        c.instance_badges = [
            {"label": instance.label,
             "badges": model.UserBadge.all(instance=instance)} for
            instance in instances]
        defaults = {'badge': [str(badge.id) for badge in c.page_user.badges]}
        return formencode.htmlfill.render(
            render("/user/badges.html"),
            defaults=defaults,
            force_defaults=False)

    @RequireInternalRequest()
    @validate(schema=UserBadgesForm(), form='badges')
    @guard.perm('instance.admin')
    def update_badges(self, id):
        user = get_entity_or_abort(model.User, id)
        badges = self.form_result.get('badge')

        if not has('global.admin'):
            # instance admins may only add user badges limited to this instance

            for badge in badges:
                if not badge.instance == c.instance:
                    h.flash(_(u'Invalid badge choice.'), u'error')
                    redirect(h.entity_url(user))

        creator = c.user

        added = []
        removed = []
        for badge in user.badges:
            if badge not in badges:
                removed.append(badge)
                user.badges.remove(badge)

        for badge in badges:
            if badge not in user.badges:
                badge.assign(user, creator)
                added.append(badge)

        model.meta.Session.flush()
        # FIXME: needs commit() cause we do an redirect() which raises
        # an Exception.
        model.meta.Session.commit()
        update_entity(user, model.UPDATE)
        redirect(h.entity_url(user, instance=c.instance))

    def _common_metadata(self, user, member=None, add_canonical=False):
        bio = user.bio
        if not bio:
            bio = _("%(user)s is using Adhocracy, a democratic "
                    "decision-making tool.") % {'user': c.page_user.name}
        description = h.truncate(text.meta_escape(bio), length=200,
                                 whole_word=True)
        h.add_meta("description", description)
        h.add_meta("dc.title", text.meta_escape(user.name))
        h.add_meta("dc.date", user.access_time.strftime("%Y-%m-%d"))
        h.add_meta("dc.author", text.meta_escape(user.name))
        h.add_rss(_("%(user)ss Activity") % {'user': user.name},
                  h.entity_url(user, format='rss'))
        if c.instance and not user.is_member(c.instance):
            h.flash(_("%s is not a member of %s") % (user.name,
                                                     c.instance.label),
                    'notice')
        if user.banned:
            h.flash(_("%s is banned from the system.") % user.name, 'notice')

    @classmethod
    def email_is_blacklisted(self, email):
        if email is None:
            return False
        listed = config.get('adhocracy.registration.email.blacklist', '')
        listed = listed.replace(',', ' ').replace('.', '').split()
        email = email.replace('.', '')
        if email in listed:
            return True
        else:
            return False

    def welcome(self, id, token):
        # Intercepted by WelcomeRepozeWho, only errors go in here
        h.flash(_('You already have a password - use that to log in.'),
                'error')
        return redirect(h.base_url('/login'))

    @RequireInternalRequest(methods=['POST'])
    @guard.perm('global.admin')
    def generate_welcome_link(self, id):
        if not can_welcome():
            return ret_abort(_("Requested generation of welcome codes, but "
                               "welcome functionality"
                               "(adhocracy.enable_welcome) is not enabled."),
                             code=403)

        page_user = get_entity_or_abort(model.User, id,
                                        instance_filter=False)
        if not page_user.welcome_code:
            page_user.welcome_code = random_token()
            model.meta.Session.add(page_user)
            model.meta.Session.commit()
        url = welcome_url(page_user, page_user.welcome_code)
        h.flash(_('The user can now log in via %s') % url, 'success')
        redirect(h.entity_url(page_user))
