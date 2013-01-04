from datetime import datetime
import logging

from pylons.i18n import _
from repoze.who.api import get_api

import authentication
import authorization
import csrf

log = logging.getLogger(__name__)


RETURN_TEMPLATE = 'return_template'
RETURN_AUTH_CHECK = 'return_auth_check'
RETURN_BOOL = 'return_bool'


def login_user(user, request, response):
    '''
    log an user in.

    *user* (:class:`adhocracy.model.User`)
         The user as whom to login
    *request* (:class:`webob.request.Request`)
         The current request object to return to the user
    '''
    identity = {'repoze.who.userid': str(user.user_name),
                'timestamp': int(datetime.utcnow().strftime("%s")),
                'user': user}

    api = get_api(request.environ)
    for name, identifier in api.identifiers:
        if identity is not None:
            headers = identifier.remember(request.environ, identity)
            if headers is not None:
                response.headerlist.extend(headers)


class AuthModuleWrapper(object):
    """ dirty hack providing syntactic suger like ``can.proposal.create``"""

    import proposal
    import comment
    import tag
    import user
    import poll
    import delegation
    import page
    import instance
    import watch
    import norm
    import selection
    import variant
    import milestone
    import badge


class RecursiveAuthWrapper(object):
    """ dirty hack providing syntactic suger like ``can.proposal.create``"""

    def __init__(self, obj, raise_type):
        self.obj = obj
        self.raise_type = raise_type

    def __getattr__(self, attr):
        orig = getattr(self.obj, attr)
        return RecursiveAuthWrapper(orig, self.raise_type)

    def __call__(self, *a, **kw):
        auth_check = authorization.AuthCheck(method=self.obj.func_name)
        self.obj(auth_check, *a, **kw)

        if self.raise_type == RETURN_AUTH_CHECK:
            return auth_check

        elif self.raise_type == RETURN_BOOL:
            return bool(auth_check)

        else:
            assert(self.raise_type == RETURN_TEMPLATE)
            if auth_check:
                return auth_check
            elif auth_check.need_login():
                # Authentication might help
                from adhocracy.lib.helpers import login_redirect_url
                from pylons.controllers.util import redirect
                redirect(login_redirect_url())
            else:
                from adhocracy.lib.templating import ret_abort
                log.debug("Aborting due to authorisation error: %s" %
                          repr(self.obj))
                ret_abort(_("We're sorry, but it seems that you lack the "
                            "permissions to continue."), code=403)


auth_module_wrapper = AuthModuleWrapper()

require = RecursiveAuthWrapper(auth_module_wrapper, RETURN_TEMPLATE)
check = RecursiveAuthWrapper(auth_module_wrapper, RETURN_AUTH_CHECK)
can = RecursiveAuthWrapper(auth_module_wrapper, RETURN_BOOL)
