from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import redirect
from adhocracy.lib.base import BaseController
from adhocracy.lib import event
import requests
from adhocracy.lib.auth import login_user
from adhocracy.model.velruse import Velruse
from adhocracy import model
from adhocracy.model.user import User
from json import loads, dumps
from adhocracy.lib import helpers as h
import random
from pylons.i18n import _
import logging
log = logging.getLogger(__name__)
from adhocracy.lib.auth.authentication import allowed_login_types


def unused_user_name(preferred_user_name):
    """
    Will find an adhocracy username which is not used
    but similiar to the given one.
    It doesn't account for names too long.
    """

    if User.find_by_user_name(preferred_user_name) is None:
        return preferred_user_name
    else:
        random_digit = random.randint(0, 9)
        return unused_user_name(preferred_user_name + str(random_digit))


def update_email_trust(adhocracy_user, velruse_email):
    if adhocracy_user.email == velruse_email:
        adhocracy_user.set_email_verified()


#TODO:
#       right now, it only works with verified emails,
#       but facebook handles that
class VelruseController(BaseController):

    def logged_in(self):
        """
        Recieves authentication messages from the velruse service.
        It will log in users or connect their adhocracy account
        to the authentication data given by velruse.
        It also creates adhocracy accounts if it thinks the user has none.
        """

        token = request.params['token']
        payload = {'format': 'json', 'token': token}
        rsp = requests.get(h.velruse_url('/auth_info'),
                           params=payload,
                           timeout=1)
        if rsp.status_code >= 400:
            return self._failure('Internal server error:'
                                 'velruse service not available.')

        auth_info = loads(rsp.content)
        log.debug('received auth_info from velruse:\n' +
                  '<pre>' + dumps(auth_info, indent=4) + '</pre>')

        if 'error' in auth_info:
            error = auth_info['error']
            if error == 'user_denied':
                return self._failure(_('Login failed: ') +
                                     _('You have to give Adhocracy permission '
                                       'to connect to your Facebook account.'),
                                     auth_info)
            else:
                return self._failure(_('Login failed: ') + auth_info['error'],
                                     auth_info)

        provider_name = auth_info['provider_name']

        if provider_name not in allowed_login_types():
            self._failure("Logging in with %s "
                          "is not allowed on this installation."
                          % provider_name.capitalize(),
                          auth_info)
        else:
            profile = auth_info['profile']
            email = profile['verifiedEmail']
            display_name = profile['displayName']
            preferred_name = profile['preferredUsername'].replace('.', '_')
            user_name = unused_user_name(preferred_name)

            accounts = profile['accounts']
            velruse_user = Velruse.find_any(accounts)

            if c.user:
                adhocracy_user = c.user
            elif velruse_user:
                adhocracy_user = velruse_user.user
            else:
                adhocracy_user = None

            if velruse_user:
                domain = velruse_user.domain
                domain_user = velruse_user.domain_user
            else:
                domain = accounts[0]['domain']
                domain_user = accounts[0]['userid']

            # login right away
            if adhocracy_user and velruse_user:
                update_email_trust(adhocracy_user, email)
                self._login(velruse_user)

            # create new user in both Velruse and User and login
            elif not adhocracy_user and not velruse_user:
                new_user = self._create(user_name,
                                        email,
                                        domain,
                                        domain_user,
                                        email_verified=True,
                                        display_name=display_name)

                adhocracy_user, velruse_user = new_user
                self._login(velruse_user)

            # create new user in Velruse for a logged in user
            elif adhocracy_user and not velruse_user:
                self._connect(adhocracy_user, domain, domain_user,
                              provider_name,
                              email, email_verified=True)

            # error case
            elif not adhocracy_user and velruse_user:
                raise "internal error (database inconsistent)"
            else:
                raise "internal error (impossible)"

    def _login(self, velruse_user):
        """
        Log the user in and redirect him to a sane place.
        """

        adhocracy_user = velruse_user.user
        if adhocracy_user:
            login_user(adhocracy_user, request, response)
            session['login_type'] = 'velruse'
            if c.instance and not adhocracy_user.is_member(c.instance):
                redirect(h.base_url("/instance/join/%s?%s" % (c.instance.key,
                                                              h.url_token())))
            redirect(h.user.post_login_url(adhocracy_user))

        # FIXME: what happens adhocracy_user is None?
        # ANSWER: should be impossible, velruse_user.user_id is not NULLable
        #         and velruse_user.user is found
        #         with velruse_user.user_id (by SQLAlchemy)

    def _failure(self, message, auth_info=None):
        """
        Abort a velruse authenication attempt and return to login page,
        giving an error message at the openif / velruse area.
        """

        log.info('velruse login error: ' + message)
        if auth_info:
            log.debug('<pre>' + dumps(auth_info, indent=4) + '</pre>')

        h.flash(message, 'error')
        if c.user:
            return redirect(h.entity_url(c.user, member='edit'))
        else:
            redirect("/login")

    def _create(self, user_name, email, domain, domain_user,
                email_verified=False, display_name=None):
        """
        Create a user based on data gathered from velruse.
        """

        user = User.find_by_email(email)
        if user is None:
            user = model.User.create(user_name,
                                     email,
                                     locale=c.locale,
                                     display_name=display_name)

        if email_verified:
            user.set_email_verified()

        v = Velruse(unicode(domain), unicode(domain_user), user)
        model.meta.Session.add(v)
        model.meta.Session.commit()

        event.emit(event.T_USER_CREATE, user)
        return user, v

    def _connect(self, adhocracy_user, domain, domain_user,
                 provider_name,
                 velruse_email, email_verified=False):
        """
        Connect existing adhocracy user to velruse.
        """

        if Velruse.any_by_user(adhocracy_user) is None:
            velruse_user = Velruse.connect(adhocracy_user, domain, domain_user,
                                           velruse_email, email_verified)

            h.flash(_("You successfully connected to %s."
                      % provider_name.capitalize()),
                    'success')

            redirect(h.user.post_login_url(adhocracy_user))
            return velruse_user

        else:
            h.flash(_("Your %s account is already connected."
                      % provider_name.capitalize()),
                    'error')

            redirect(h.user.post_login_url(adhocracy_user))
            return None
