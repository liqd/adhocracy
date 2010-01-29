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

def RequireInternalRequest(methods=['POST', 'GET', 'PUT', 'DELETE']):
    """
    XSRF Spoof Filter
    
    TODO: There is still a scenario in which an attacker opens an adhocracy 
    page in an iframe, extracts a valid modtoken via javascript and uses this
    token to execute the request. 
    """
    def _decorate(f, *a, **kw):
        def check():
            if not request.method in methods:
                return True
            if not request.environ.get("AUTH_TYPE") == "cookie":
                return True
            if config.get('skip_authentication'):
                return True
            
            if request.environ.get('HTTP_REFERER'):           
                ref_url = urlparse(request.environ.get('HTTP_REFERER'))
                ref_host = ref_url.hostname
                if ref_url.port:
                    ref_host += ":" + str(ref_url.port)
            
                if ref_host.endswith(request.environ['adhocracy.domain']):
                    if request.method != 'GET':
                        return True
            
            if request.method == 'GET' and has_token():
                return True
                       
            return False
        if check():
            return f(*a, **kw)
        else:
            abort(403, _("Action failed. You were probably trying to re-perform " +
                         "an action after using your browser's 'Back' button. This " +
                         "is prohibited for security reasons.")) 
    return decorator(_decorate)

def make_token():
    tokens = session.get('modtokens', [])
    
    token = None
    if len(tokens) < 100:
        token = hashlib.sha1(str(random.random())).hexdigest()
    else:
        token = tokens[-1]
        
    tokens.append(token)
    session['modtokens'] = tokens
    session.save()
    return token

def url_token():
    return "_csrftoken=%s" % make_token()

def field_token():
    return '<input name="_csrftoken" type="hidden" value="%s" />' % make_token() 

def has_token():
    if request.params.get('_csrftoken', None) in session['modtokens']:
        tokens = session['modtokens']
        tokens.remove(request.params.get('_csrftoken'))
        session['modtokens'] = tokens
        session.save()
        return True
    return False
