from urllib import urlencode
import formencode
from pylons import request
from pylons import response
from pylons import session
from pylons.controllers.util import redirect
from pylons.i18n import _
from adhocracy import config
from adhocracy import forms
from adhocracy.lib import helpers as h
from adhocracy.lib.auth import login_user
from adhocracy.lib.auth.authentication import allowed_login_types
from adhocracy.lib.auth.csrf import check_csrf
from adhocracy.lib.auth.shibboleth import get_attribute
from adhocracy.lib.auth.shibboleth import USERBADGE_MAPPERS
from adhocracy.lib.auth.shibboleth import DISPLAY_NAME_FUNCTIONS
from adhocracy.lib.base import BaseController
from adhocracy.lib.staticpage import add_static_content
from adhocracy.lib.templating import render
from adhocracy.lib.templating import ret_abort
from adhocracy.model import meta
from adhocracy.model.user import User
from adhocracy.model.badge import UserBadge


class ShibbolethRegisterForm(formencode.Schema):
    _tok = formencode.validators.String()
    if not config.get_bool('adhocracy.force_randomized_user_names'):
        username = formencode.All(
            formencode.validators.PlainText(not_empty=True),
            forms.UniqueUsername(),
            forms.ContainsChar())
    if config.get_bool('adhocracy.set_display_name_on_register'):
        display_name = formencode.validators.String(not_empty=False,
                                                    if_missing=None)
    email = formencode.All(formencode.validators.Email(
        not_empty=config.get_bool('adhocracy.require_email')),
        forms.UniqueEmail())
    # store custom attributes checkboxes


class ShibbolethController(BaseController):
    """
    The reason not to use a proper repoze.who plugin is that such a plugin
    would be very hard to understand as the repoze.who API doesn't fit the
    Shibboleth requirements very well (we first did that and it was ugly).
    """

    def request_auth(self):
        if 'shibboleth' not in allowed_login_types():
            ret_abort(_("Shibboleth authentication not enabled"), code=403)

        came_from = request.GET.get('came_from', '/')

        came_from_qs = urlencode({'came_from': came_from})
        shib_qs = urlencode(
            {'target': '/shibboleth/post_auth?%s' % came_from_qs})

        redirect('/Shibboleth.sso/Login?%s' % shib_qs)

    def post_auth(self):
        """
        This controller is called after successful Shibboleth authentication.
        It checks whether the authenticated user already exists. If yes, the
        corresponding Adhocracy user is logged in. If no, an intermediate step
        querying the user for additional information is performed and a new
        Adhocracy user is registered.

        In any case the Shibboleth headers are only used once for logging in
        and immediatly removed afterwards. The reason for this design decision
        is that Single-Sign-Off isn't recommended by Shibboleth as it is either
        very complicated or even impossible.

        NOTE: There isn't one clear way on how to deal with user deletion in
        environments with external user management. We now implemented the
        following:
        If a user logs in into a deleted account, this account is undeleted
        on the fly.
        """
        if 'shibboleth' not in allowed_login_types():
            ret_abort(_("Shibboleth authentication not enabled"), code=403)

        persistent_id = self._get_persistent_id()
        if persistent_id is None:
            ret_abort(_("This URL shouldn't be called directly"), code=403)

        user = User.find_by_shibboleth(persistent_id, include_deleted=True)

        if user is not None:
            if user.is_deleted():
                user.undelete()
                meta.Session.commit()
                h.flash(_("User %s has been undeleted") % user.user_name,
                        'success')
            return self._login(user, h.user.post_login_url(user))
        else:
            return self._register(persistent_id)

    def _get_persistent_id(self):
        return request.environ.get('HTTP_PERSISTENT_ID', None)

    def _login(self, user, target):
        self._update_userbadges(user)

        if config.get_bool('adhocracy.shibboleth.display_name.force_update'):
            display_name = self._get_display_name()
            if display_name is not None:
                user.display_name = display_name
                meta.Session.commit()

        login_user(user, request, response)
        session['login_type'] = 'shibboleth'

        came_from = request.GET.get('came_from', target)
        qs = urlencode({'return': came_from})

        return redirect('/Shibboleth.sso/Logout?%s' % qs)

    def _register_form(self, defaults=None, errors=None):

        data = {
            'email_required': (config.get_bool('adhocracy.require_email')),
        }
        add_static_content(data,
                           u'adhocracy.static_shibboleth_register_ontop_path',
                           body_key=u'body_ontop')
        add_static_content(data,
                           u'adhocracy.static_shibboleth_register_below_path',
                           body_key=u'body_below', title_key=u'_ignored')
        return formencode.htmlfill.render(
            render("/shibboleth/register.html", data),
            defaults=defaults, errors=errors,
            force_defaults=False)

    def _create_user_and_login(self, persistent_id, username, email=None,
                               display_name=None, locale=None):
        user = User.create(username,
                           email,
                           locale=locale,
                           display_name=display_name,
                           shibboleth_persistent_id=persistent_id,
                           omit_activation_code=(email is not None))
        # NOTE: We might want to automatically join the current instance
        # here at some point

        meta.Session.commit()
        return self._login(user, h.user.post_register_url(user))

    def _register(self, persistent_id):

        # initializing user data dict
        user_data = {}

        user_data['email'] = get_attribute(request, 'shib-email', None)

        if config.get_bool('adhocracy.force_randomized_user_names'):
            user_data['username'] = None
        else:
            user_data['username'] = get_attribute(request, 'shib-username')

        user_data['display_name'] = self._get_display_name()

        locale_attribute = config.get("adhocracy.shibboleth.locale.attribute")
        if locale_attribute is not None:
            user_data['locale'] = get_attribute(request, locale_attribute)

        # what to do
        if request.method == 'GET':
            if config.get_bool('adhocracy.shibboleth.register_form'):
                # render a form for missing uaser data
                return self._register_form(defaults=user_data)
            else:
                # register_form is False -> user data should be complete
                return self._create_user_and_login(persistent_id, **user_data)

        else:  # POST
            check_csrf()

            try:
                form_result = ShibbolethRegisterForm().to_python(
                    request.POST)

                user_data['username'] = form_result.get(
                    'username', user_data['username'])
                user_data['display_name'] = form_result.get(
                    'display_name', user_data['display_name'])
                user_data['email'] = form_result.get(
                    'email', user_data['email'])

                return self._create_user_and_login(persistent_id, **user_data)

            except formencode.Invalid, i:
                return self._register_form(errors=i.unpack_errors())

    def _get_display_name(self):
        display_name_function = config.get_json(
            "adhocracy.shibboleth.display_name.function")
        if display_name_function is not None:
            function = display_name_function["function"]
            kwargs = display_name_function["args"]
            display_name = DISPLAY_NAME_FUNCTIONS[function](request, **kwargs)
        else:
            display_name = None
        return display_name

    def _update_userbadges(self, user):

        mappings = config.get_json("adhocracy.shibboleth.userbadge_mapping")

        is_modified = False

        for m in mappings:
            badge_title = m["title"]
            function_name = m["function"]
            kwargs = m["args"]

            badge = UserBadge.find(badge_title)
            if badge is None:
                raise Exception('configuration expects badge "%s"'
                                % badge_title)
            want_badge = USERBADGE_MAPPERS[function_name](request, **kwargs)
            has_badge = badge in user.badges

            if want_badge and not has_badge:
                # assign badge
                badge.assign(user=user, creator=user)
                is_modified = True
            elif has_badge and not want_badge:
                # unassign badge
                user.badges.remove(badge)
                is_modified = True

        if is_modified:
            meta.Session.commit()
