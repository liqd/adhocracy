import logging
from pylons.i18n import _

import authentication
import authorization
import csrf

log = logging.getLogger(__name__)


RETURN_TEMPLATE = 'return_template'
RETURN_AUTH_CHECK = 'return_auth_check'
RETURN_BOOL = 'return_bool'


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
            else:
                from adhocracy.lib.templating import ret_abort
                log.debug("Aborting due to error with permission: %s" %
                          repr(self.obj))
                ret_abort(_("We're sorry, but it seems that you lack the "
                            "permissions to continue."), code=403)


auth_module_wrapper = AuthModuleWrapper()

require = RecursiveAuthWrapper(auth_module_wrapper, RETURN_TEMPLATE)
check = RecursiveAuthWrapper(auth_module_wrapper, RETURN_AUTH_CHECK)
can = RecursiveAuthWrapper(auth_module_wrapper, RETURN_BOOL)
