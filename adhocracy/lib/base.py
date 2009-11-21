"""The base Controller API

Provides the BaseController class for subclassing.
"""
import logging

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
from templating import render, NamedPager
import adhocracy.model as model
import search as libsearch
import helpers as h
import event
import democracy
import tiles
import sorting
import watchlist
import text.i18n as i18n


class BaseController(WSGIController):
        
    def _parse_motion_id(self, id):       
        c.motion = model.Motion.find(id)
        if not c.motion:
            abort(404, _("No motion with ID %(id)s exists.") % {'id': id})  

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        import adhocracy.lib 
        c.lib = adhocracy.lib 
        c.model = model
        c.instance = model.filter.get_instance()
                
        libsearch.attach_thread()
        
        environ['HTTP_HOST'] = environ['HTTP_HOST_ORIGINAL']
               
        if environ.get('repoze.who.identity'):
            c.user = environ.get('repoze.who.identity').get('user')
            #model.meta.Session.add(c.user)
        else:
            c.user = None
             
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
            return WSGIController.__call__(self, environ, start_response)
        finally:
            model.meta.Session.remove()





def ExpectFormat(formats=['html', 'rss', 'xml', 'json']):
    def _parse(f, *a, **kw):
        #TODO
        return f(*a, **kw)
    return decorator(_parse)
