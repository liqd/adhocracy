from datetime import datetime
from functools import partial
import logging

from decorator import decorator

from pylons.i18n import _
from repoze.who.api import get_api

import authentication
import authorization
import csrf

log = logging.getLogger(__name__)


RETURN_TEMPLATE = 'return_template'
RETURN_AUTH_CHECK = 'return_auth_check'
RETURN_BOOL = 'return_bool'
RETURN_DECORATOR = 'return_decorator'


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
    """ Helper class for RecursiveAuthWrapper """

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
    import message

    @staticmethod
    def perm(check, permission):
        """
        Checks that the current user has the given permission.
        """
        check.perm(permission)


class RecursiveAuthWrapper(object):
    """
    Dirty hack providing various syntactic sugar in order to perform
    authorization checks.

    Return an error template if a check isn't fulfilled, otherwise pass:

    >>> require.proposal.edit(p)

    Return a bool for a check:

    >>> can.proposal.index()

    Return an AuthCheck object, which can be queried further:

    >>> check.proposal.create()

    Decorate a controller function:

    >>> @guard.proposal.create()
    ... def create(self):
    ...     pass
    """

    def __init__(self, obj, raise_type):
        self.obj = obj
        self.raise_type = raise_type
        self.closure = None

    def __getattr__(self, attr):
        orig = getattr(self.obj, attr)
        return RecursiveAuthWrapper(orig, self.raise_type)

    def __call__(self, *a, **kw):

        if self.raise_type == RETURN_DECORATOR:

            # The decorator library is used, as Pylons seems to inspect the
            # signature of the controller methods and dynamically call
            # kwargs as args. The decorator library makes sure the decorated
            # method is signature preserving and the Pylons magic keeps
            # working.

            @decorator
            def wrapper(decorated_fun, *args, **kwargs):

                self.closure = partial(decorated_fun, *args, **kwargs)
                return self.check(*a, **kw)

            return wrapper

        else:
            return self.check(*a, **kw)

    def check(self, *a, **kw):

        auth_check = authorization.AuthCheck(method=self.obj.__name__)
        self.obj(auth_check, *a, **kw)

        if self.raise_type == RETURN_AUTH_CHECK:
            return auth_check

        elif self.raise_type == RETURN_BOOL:
            return bool(auth_check)

        else:
            assert(self.raise_type in [RETURN_TEMPLATE, RETURN_DECORATOR])
            if auth_check:
                if self.raise_type == RETURN_DECORATOR:
                    return self.closure()
                else:
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
guard = RecursiveAuthWrapper(auth_module_wrapper, RETURN_DECORATOR)
