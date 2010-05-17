import logging
from pylons.i18n import _

import authentication
import authorization
import csrf

log = logging.getLogger(__name__)

class _can(object):
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
    
can = _can()


class _require(object):
    
    def __init__(self, obj):
        self.obj = obj
    
    def __getattr__(self, attr):
        orig = getattr(self.obj, attr)
        return _require(orig)
        
    def __call__(self, *a, **kw):
        ret = self.obj(*a, **kw)
        if not ret:
            from adhocracy.lib.templating import ret_abort
            log.debug("Aborting due to error with permission: %s" % repr(self.obj))
            ret_abort(_("We're sorry, but it seems that you lack the permissions to continue."), code=403)
        return ret
            
require = _require(can)
            