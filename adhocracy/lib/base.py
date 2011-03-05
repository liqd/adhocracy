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
from paste.deploy.converters import asbool

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
from auth import can, require
from templating import render, render_json, render_png
from templating import ret_success, ret_abort
from pager import NamedPager
from static import StaticPage
from util import get_entity_or_abort
import adhocracy.model as model
import adhocracy.i18n as i18n
import search as libsearch
import helpers as h
import event
import democracy
import tiles
import sorting
import watchlist
import pager


log = logging.getLogger(__name__)

from pprint import pprint
class BaseController(WSGIController):
    
    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        #pprint(request.environ)
        c.instance = model.instance_filter.get_instance()
        c.user = environ.get('repoze.who.identity', {}).get('user')
        if c.user.banned or c.user.delete_time: 
            c.user = None
        c.active_controller = request.environ.get('pylons.routes_dict')\
            .get('controller')
        c.debug = asbool(config.get('debug'))
        i18n.handle_request()
        
        if c.instance:
            h.add_rss("%s News" % c.instance.label, 
                      h.base_url(c.instance, '/instance/%s.rss' % c.instance.key))
        
        h.add_meta("description", _("A liquid democracy platform for making decisions in " 
                   + "distributed, open groups by cooperatively creating proposals and voting "
                   + "on them to establish their support."))
        h.add_meta("keywords", _("adhocracy, direct democracy, liquid democracy, liqd, democracy, wiki, voting," 
                   + "participation, group decisions, decisions, decision-making"))
        
        try:
            begin_time = time()
            return WSGIController.__call__(self, environ, start_response)
        except Exception, e:
            log.exception(e) 
            model.meta.Session.rollback()
            raise
        finally:
            model.meta.Session.remove()
            #log.debug(u"Rendering page took %sms" % ((time()-begin_time)*1000))
    
    def bad_request(self, format='html'):
        log.debug("400 Request: %s" % request.params)
        return ret_abort(_("Invalid request. Please go back and try again."), 
                         code=400, format=format)
    
        
    def not_implemented(self, format='html'):
        return ret_abort(_("The method you used is not implemented."), 
                         code=400, format=format)
    


