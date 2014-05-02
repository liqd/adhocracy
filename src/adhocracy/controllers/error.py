import cgi
import re

from pylons import request, response, tmpl_context as c
from pylons.i18n import _
from pylons.i18n import lazy_ugettext
from pylons.controllers.util import abort

from paste.urlparser import PkgResourcesParser
from pylons.controllers.util import forward

from adhocracy import config
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render

BODY_RE = re.compile("<br \/><br \/>(.*)<\/body", re.S)


ERROR_MESSAGES = {
    404: lazy_ugettext(u"The requested page could not be found."),
    503: lazy_ugettext(u"The system is currently down for maintenance. "
                       u"Please check back soon!"),
}
ERROR_NAMES = {
    400: lazy_ugettext('Bad Request'),
    401: lazy_ugettext('Unauthorized'),
    403: lazy_ugettext('Forbidden'),
    404: lazy_ugettext('Not Found'),
    418: lazy_ugettext('I\'m a teapot'),
    500: lazy_ugettext('Internal Server Error'),
    503: lazy_ugettext('Service Unavailable'),
}


class ErrorController(BaseController):

    """Generates error documents as and when they are required.

    The StatusCodeRedirect middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    StatusCodeRedirect middleware in your config/middleware.py file.

    """

    identifier = "error"

    def document(self):
        resp = request.environ.get('pylons.original_response')
        if resp is None:
            raise abort(404)
        response.status = resp.status
        if resp.content_type == 'text/javascript':
            response.content_type == resp.content_type
            return resp.body

        c.error_code = resp.status_int

        c.hide_notify = (c.error_code not in [400, 500])

        # Try to extract error message from environment, e.g.
        # adhocracy.lib.templating.ret_status sets this.
        c.error_message = request.environ.get('adhocracy.error_message')

        if not c.error_message:
            # Try to extract error message from stub response
            for match in BODY_RE.finditer(resp.body):
                c.error_message = match.group(1).strip()

        if not c.error_message:
            # Fallback to default empty message
            c.error_message = ERROR_MESSAGES.get(c.error_code, '')

        c.error_name = ERROR_NAMES.get(c.error_code, '')

        if config.get_bool('adhocracy.interactive_debugging'):
            c.trace_url = request.environ['pylons.original_response']\
                .headers.get('X-Debug-URL', None)

            if c.trace_url is not None:
                # this may only happen in debug mode
                assert(config.get_bool('debug', False))
        else:
            c.trace_url = None

        return render("/error/http.html")

    def show(self):
        """Force an error message.

        Always return status 200, but render the HTML error message.
        """
        if not config.get_bool('debug'):
            raise abort(404)
        status = request.GET.get('force_status')
        if status is None:
            raise abort(404)
        data = {
            'hide_code': 'hide_code' in request.GET,
            'hide_notify': 'hide_notify' in request.GET,
            'error_code': int(status),
            'error_name': ERROR_NAMES.get(int(status), ''),
            'error_message': ERROR_MESSAGES.get(int(status), ''),
        }
        return render("/error/http.html", data)

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
