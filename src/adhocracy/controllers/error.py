import cgi
import re

from pylons import request, response, tmpl_context as c
from pylons.i18n import _
from pylons import config
from pylons.controllers.util import abort

from paste.deploy.converters import asbool
from paste.urlparser import PkgResourcesParser
from pylons.controllers.util import forward

from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render

BODY_RE = re.compile("<br \/><br \/>(.*)<\/body", re.S)


class ErrorController(BaseController):

    """Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.

    """

    def document(self):
        resp = request.environ.get('pylons.original_response')
        if resp is None:
            raise abort(404)
        response.status = resp.status
        if resp.content_type == 'text/javascript':
            response.content_type == resp.content_type
            return resp.body

        # YOU DO NOT SEE THIS. IF YOU DO, ITS NOT WHAT IT LOOKS LIKE
        # I DID NOT HAVE REGEX RELATIONS WITH THAT HTML PAGE
        for match in BODY_RE.finditer(resp.body):
            c.error_message = match.group(1)

        c.error_code = cgi.escape(request.GET.get('code',
                                                  str(resp.status_int)))

        if not c.error_message:
            c.error_message = _("Error %s") % c.error_code

        if asbool(config.get('adhocracy.interactive_debugging', 'false')):
            c.trace_url = request.environ['pylons.original_response']\
                .headers.get('X-Debug-URL', None)

            if c.trace_url is not None:
                # this may only happen in debug mode
                assert(asbool(config.get('debug', 'false')))
        else:
            c.trace_url = None

        return render("/error/http.html")

    def img(self, id):
        """Serve Pylons' stock images"""
        return self._serve_file('/'.join(['media/img', id]))

    def style(self, id):
        """Serve Pylons' stock stylesheets"""
        return self._serve_file('/'.join(['media/style', id]))

    def _serve_file(self, path):
        """Call Paste's FileApp (a WSGI application) to serve the file
        at the specified path
        """
        request.environ['PATH_INFO'] = '/%s' % path
        return forward(PkgResourcesParser('pylons', 'pylons'))
