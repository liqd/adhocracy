"""The base Controller API

Provides the BaseController class for subclassing.
"""
import logging
from time import time

from pylons import config
from pylons.controllers import WSGIController
from pylons import request, response, session, tmpl_context as c, g
from pylons.controllers.util import abort, redirect_to
from pylons.decorators import validate
from pylons.i18n import _, add_fallback, get_lang, set_lang, gettext

import routes

import formencode
import formencode.validators as validators
from formencode import htmlfill

from authorization import has_permission
import authorization as auth
from repoze.what.plugins.pylonshq import ActionProtector

from cache import memoize
from instance import RequireInstance
from xsrf import RequireInternalRequest
from templating import render, NamedPager, StaticPage
from util import get_entity_or_abort
import adhocracy.model as model
import search as libsearch
import helpers as h
import event
import democracy
import tiles
import sorting
import watchlist
#import microblog
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
                        
        environ['HTTP_HOST'] = environ['HTTP_HOST_ORIGINAL']
               
        if environ.get('repoze.who.identity'):
            c.user = environ.get('repoze.who.identity').get('user')
            #model.meta.Session.merge(c.user)
        else:
            c.user = None
             
        #if c.instance is not None:
        #    model.meta.Session.merge(c.instance)
             
        # have to do this with the user in place
        i18n.handle_request()
                    
        if c.user:
            h.add_rss(_("My Adhocracies"), h.instance_url(None, '/feed.rss'))
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


def ExpectFormat(formats=['html', 'rss', 'xml', 'json']):
    def _parse(f, *a, **kw):
        #TODO
        return f(*a, **kw)
    return decorator(_parse)
