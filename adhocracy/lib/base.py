"""The base Controller API

Provides the BaseController class for subclassing.
"""
import logging
from time import time

from pylons import config
from pylons.controllers import WSGIController
from pylons import request, response, session, tmpl_context as c, g
from pylons.controllers.util import abort, redirect
from pylons.decorators import validate
from pylons.i18n import _, add_fallback, get_lang, set_lang, gettext

import routes

import formencode
import formencode.validators as validators
from formencode import htmlfill
import simplejson

from auth.authorization import has_permission
import auth.authorization as auth
from repoze.what.plugins.pylonshq import ActionProtector

from cache import memoize
from instance import RequireInstance
from auth.csrf import RequireInternalRequest, token_id
from templating import render, render_json, render_png
from pager import NamedPager
from static import StaticPage
from util import get_entity_or_abort
import adhocracy.model as model
import search as libsearch
import helpers as h
import event
import democracy
import tiles
import sorting
import watchlist
import rest
import pager
import text.i18n as i18n

log = logging.getLogger(__name__)

class BaseController(WSGIController):
    
    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        
        import adhocracy.lib
        c.lib = adhocracy.lib 
        c.model = model
        c.instance = model.filter.get_instance()
        c.user = environ.get('repoze.who.identity', {}).get('user', None)
        
        # http host information was moved around to mess with repoze.who                 
        #environ['HTTP_HOST'] = environ.get('HTTP_HOST_ORIGINAL')
        
        #from pprint import pprint
        #pprint(environ)
        #pprint(environ.get('repoze.who.identity').items())
        #print "SESSION ", session.id
        
        # get RESTish:
        #self._parse_REST_request()
        
        # have to do this with the user in place
        i18n.handle_request()
        
        if c.instance:
            h.add_rss("%s News" % c.instance.label, 
                      h.instance_url(c.instance, '/instance/%s.rss' % c.instance.key))
        
        h.add_meta("description", _("A liquid democracy platform for making decisions in " 
                   + "distributed, open groups by cooperatively creating proposals and voting "
                   + "on them to establish their support."))
        h.add_meta("keywords", _("adhocracy, direct democracy, liquid democracy, liqd, democracy, wiki, voting," 
                   + "participation, group decisions, decisions, decision-making"))
        
        try:
            begin_time = time()
            return WSGIController.__call__(self, environ, start_response)
        except: 
            model.meta.Session.rollback()
            raise
        finally:
            model.meta.Session.remove()
            model.meta.Session.close()
            log.debug("Rendering page %s took %sms" % (environ.get('PATH_INFO'), ((time()-begin_time)*1000)))
    
    
    def _parse_REST_request(self):
        if request.method not in ['POST', 'PUT']:
            return
        if request.content_type == "text/javascript":
            if request.method == 'POST':
                request.POST = simplejson.loads(request.body)
                request.params.update(request.POST)
            elif request.method == 'PUT':
                request.PUT = simplejson.loads(request.body)
                request.POST.update(request.PUT)
                request.params.update(request.PUT)
            
    def bad_request(self):
        log.debug("400 Request: %s" % request.params)
        abort(400, _("Invalid request. Please go back and try again."))
        
    def not_implemented(self):
        abort(400, _("The method you used is not implemented."))
    


