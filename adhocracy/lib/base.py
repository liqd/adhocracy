"""The base Controller API

Provides the BaseController class for subclassing.
"""
import logging

from paste.deploy.converters import asbool
from pylons import config
from pylons.controllers import WSGIController
from pylons import request, tmpl_context as c
from pylons.i18n import _
from sqlalchemy.orm.scoping import ScopedSession
from sqlalchemy.orm.exc import DetachedInstanceError

from adhocracy import i18n, model
from adhocracy.lib import helpers as h
from adhocracy.lib.templating import ret_abort

log = logging.getLogger(__name__)


class BaseController(WSGIController):

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        #for key in environ.keys():
        #    print key, environ[key]
        self.log_request(environ)
        
        c.instance = model.instance_filter.get_instance()
        if c.instance is not None:
            # setup a global variable to mark the current item in
            # the global navigation
            c.active_global_nav = 'instances'
        else:
            c.active_global_nav = 'home'
        c.user = environ.get('repoze.who.identity', {}).get('user')
        try:
            if c.user and (c.user.banned or c.user.delete_time):
                c.user = None
        except DetachedInstanceError, e:
            log.exception(e)
        c.active_controller = request.environ.get('pylons.routes_dict')\
            .get('controller')
        c.debug = asbool(config.get('debug'))
        i18n.handle_request()

        h.add_rss("%s News" % h.site.name(),
                  h.base_url('/feed.rss', None))
        if c.instance:
            h.add_rss("%s News" % c.instance.label,
                      h.base_url('/instance/%s.rss' % c.instance.key))

        h.add_meta("description",
                   _("A liquid democracy platform for making decisions in "
                     "distributed, open groups by cooperatively creating "
                     "proposals and voting on them to establish their "
                     "support."))
        h.add_meta("keywords",
                   _("adhocracy, direct democracy, liquid democracy, liqd, "
                     "democracy, wiki, voting,participation, group decisions, "
                     "decisions, decision-making"))

        try:
            return WSGIController.__call__(self, environ, start_response)
        except Exception, e:
            log.exception(e)
            model.meta.Session.rollback()
            raise
        finally:
            if isinstance(model.meta.Session, ScopedSession):
                model.meta.Session.remove()

    def bad_request(self, format='html'):
        log.debug("400 Request: %s" % request.params)
        return ret_abort(_("Invalid request. Please go back and try again."),
                         code=400, format=format)

    def not_implemented(self, format='html'):
        return ret_abort(_("The method you used is not implemented."),
                         code=400, format=format)

    def log_request(self, environ):
        req_user_id = 0
        req_cookies = ''
        c.user = environ.get('repoze.who.identity', {}).get('user')
        if(c.user):
            req_user_id= c.user.id
        if 'HTTP_COOKIE' in environ:
            req_cookies = environ['HTTP_COOKIE']

        req = model.Request(req_user_id, req_cookies, environ['REMOTE_ADDR'], environ['HTTP_USER_AGENT'], environ['PATH_INFO'])
        
        print "[ID]", req.user_id, "[COOKIES]", req.cookies, "[R.IP]", req.remote_ip_address, "[USERAGENT]", req.useragent, "[REQ_URL]", req.request_url
        return req
