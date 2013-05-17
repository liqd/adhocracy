"""
XSRF is Cross-Site Request Forgery, where an attacker has a user follow
a link that triggers an action on a site which the user did not
intentionally want to perform (i.e. vote in a certain way). To prevent
this, some actions are only possible if authorized via HTTP or if a
modtoken - a shared SHA1 hash - is included.
"""

import uuid
import logging
from decorator import decorator

from pylons import session, request
from pylons.i18n import _

from repoze.who.plugins.basicauth import BasicAuthPlugin

log = logging.getLogger(__name__)

KEY = "_tok"


ALL_METHODS = ['POST', 'GET', 'PUT', 'DELETE']


def check_csrf(methods=ALL_METHODS):

    method = request.environ.get('REQUEST_METHOD').upper()
    if method in methods:

        identifier = request.environ.get(
            'repoze.who.identity', {}).get('identifier')
        if (identifier is not None and
                isinstance(identifier, BasicAuthPlugin)):
            return
        if request.params.get(KEY) == token_id():
            return

    from adhocracy.lib.templating import ret_abort
    ret_abort(_("I'm sorry, it looks like we made a mistake "
                "(CSRF alert). Please try again."), code=403)


def RequireInternalRequest(methods=ALL_METHODS):
    """
    CSRF Spoof Filter

    TODO: There is still a scenario in which an attacker opens an adhocracy
    page in an iframe, extracts a valid modtoken via javascript and uses this
    token to execute the request.
    """
    def _decorate(f, *a, **kw):
        check_csrf(methods)
        return f(*a, **kw)
    return decorator(_decorate)


def token_id():
    if not KEY in session:
        session[KEY] = str(uuid.uuid4()).split("-")[-1]
        session.save()
    return session[KEY]


def url_token():
    return "%s=%s" % (KEY, token_id())


def field_token():
    return '<input name="%s" type="hidden" value="%s" />' % (KEY, token_id())
