from urllib import urlencode
import formencode
from pylons import request
from pylons import response
from pylons.controllers.util import redirect
from pylons.i18n import _
from adhocracy import config
from adhocracy import forms
from adhocracy.lib import helpers as h
from adhocracy.lib.auth import login_user
from adhocracy.lib.auth.authentication import allowed_login_types
from adhocracy.lib.auth.csrf import check_csrf
from adhocracy.lib.auth.shibboleth import get_userbadge_mapping
from adhocracy.lib.auth.shibboleth import USERBADGE_MAPPERS
from adhocracy.lib.base import BaseController
from adhocracy.lib.staticpage import add_static_content
from adhocracy.lib.templating import render
from adhocracy.lib.templating import ret_abort
from adhocracy.model import meta
from adhocracy.model.user import User
from adhocracy.model.badge import UserBadge


class ShibbolethRegisterForm(formencode.Schema):
    allow_extra_fields = True
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
        if not 'shibboleth' in allowed_login_types():
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
        if not 'shibboleth' in allowed_login_types():
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

        login_user(user, request, response)

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

    def _register(self, persistent_id):

        if request.method == 'GET':

            defaults = {
                'email': request.headers.get('shib-email'),
            }
            return self._register_form(defaults=defaults)

        # POST
        check_csrf()

        try:
            form_result = ShibbolethRegisterForm().to_python(
                request.params)

            if config.get_bool('adhocracy.force_randomized_user_names'):
                username = None
            else:
                username = form_result['username']
            user = User.create(username,
                               form_result['email'],
                               display_name=form_result['display_name'],
                               shibboleth_persistent_id=persistent_id)

            # NOTE: We might want to automatically join the current instance
            # here at some point

            meta.Session.commit()

            return self._login(user, h.user.post_register_url(user))

        except formencode.Invalid, i:
            return self._register_form(errors=i.unpack_errors())

    def _update_userbadges(self, user):

        tuples = get_userbadge_mapping()

        is_modified = False

        for t in tuples:
            badge_name = t[0]
            function_name = t[1]
            args = t[2:]

            badge = UserBadge.find(badge_name)
            want_badge = USERBADGE_MAPPERS[function_name](request, *args)
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
