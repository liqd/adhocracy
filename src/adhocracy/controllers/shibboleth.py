from urllib import urlencode
import formencode
from pylons import request
from pylons import response
from pylons.controllers.util import redirect
from pylons.i18n import _
from adhocracy import forms
from adhocracy.lib.auth import login_user
from adhocracy.lib.auth.authentication import allowed_login_types
from adhocracy.lib.auth.csrf import check_csrf
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render
from adhocracy.lib.templating import ret_abort
from adhocracy.model import meta
from adhocracy.model.user import User


class ShibbolethRegisterForm(formencode.Schema):
    allow_extra_fields = True
    username = formencode.All(formencode.validators.PlainText(not_empty=True),
                              forms.UniqueUsername(),
                              forms.ContainsChar())
    email = formencode.All(formencode.validators.Email(not_empty=False),
                           forms.UniqueEmail())
    # store_email checkbox
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
        """
        if not 'shibboleth' in allowed_login_types():
            ret_abort(_("Shibboleth authentication not enabled"), code=403)

        persistent_id = self._get_persistent_id()
        if persistent_id is None:
            ret_abort(_("This URL shouldn't be called directly"), code=403)

        user = User.find_by_shibboleth(persistent_id)

        if user is not None:
            return self._login(user)
        else:
            return self._register(persistent_id)

    def _get_persistent_id(self):
        return request.environ.get('HTTP_PERSISTENT_ID', None)

    def _login(self, user):
        login_user(user, request, response)

        came_from = request.GET.get('came_from', '/')
        qs = urlencode({'return': came_from})

        return redirect('/Shibboleth.sso/Logout?%s' % qs)

    def _register_form(self, defaults=None, errors=None):
        return formencode.htmlfill.render(
            render("/shibboleth/register.html"),
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

            user = User.create(form_result['username'],
                               form_result['email'],
                               shibboleth_persistent_id=persistent_id)

            # NOTE: We might want to automatically join the current instance
            # here at some point

            meta.Session.commit()

            return self._login(user)

        except formencode.Invalid, i:
            return self._register_form(errors=i.unpack_errors())
