from pylons.controllers.util import abort
from pylons.i18n import _

import authentication
import authorization
import csrf


class _can(object):
    import proposal
    import comment
    import tag
    import user
    
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
            abort(401, _("We're sorry, but it seems that you lack the permissions to continue."))
        return ret
            
require = _require(can)
            