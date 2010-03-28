"""
XSRF is Cross-Site Request Forgery, where an attacker has a user follow a link that triggers an 
action on a site which the user did not intentionally want to perform (i.e. vote in 
a certain way). To prevent this, some actions are only possible if authorized via HTTP or if a
modtoken - a shared SHA1 hash - is included.  
"""

import random
import hashlib
from urlparse import urlparse
from decorator import decorator

from pylons import session, request, config
from pylons.controllers.util import abort
from pylons.i18n import _

from repoze.who.plugins.basicauth import BasicAuthPlugin

KEY = "_tok"

def RequireInternalRequest(methods=['POST', 'GET', 'PUT', 'DELETE']):
    """
    CSRF Spoof Filter
    
    TODO: There is still a scenario in which an attacker opens an adhocracy 
    page in an iframe, extracts a valid modtoken via javascript and uses this
    token to execute the request. 
    """
    def _decorate(f, *a, **kw):
        def check():
            if config.get('skip_authentication'):
                return True
            
            method = request.environ.get('REQUEST_METHOD').upper()
            if not method in methods:
                print "INVALID METHOD"
                return False
            
            identifier = request.environ.get('repoze.who.identity', {}).get('identifier')
            if identifier is not None and isinstance(identifier, BasicAuthPlugin):
                return True
            
            if request.params.get(KEY) == session.id:
                return True
            
            print "WRONG ID"
            return False
        if check():
            return f(*a, **kw)
        else:
            abort(403, _("Action failed. You were probably trying to re-perform " +
                         "an action after using your browser's 'Back' button. This " +
                         "is prohibited for security reasons.")) 
    return decorator(_decorate)


def url_token():
    return "%s=%s" % (KEY, session.id)


def field_token():
    return '<input name="%s" type="hidden" value="%s" />' % (KEY, session.id)


