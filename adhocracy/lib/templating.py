import rfc822
import hashlib
import logging

from pylons import response
from pylons.controllers.util import etag_cache
from pylons.controllers.util import abort, redirect

from adhocracy.lib.helpers import json_dumps

log = logging.getLogger(__name__)

_legacy = object()
def render(template_name, data=_legacy, only_fragment=False):
    """ If only_fragment is set, render only the template itself, without
    surrounding header / footer etc."""
    if data is _legacy:
        #log.debug(u'Legacy call to render() - missing data')
        data = {}

    import adhocracy_client
    return adhocracy_client.render(template_name, data, only_fragment=only_fragment)

def render_def(template_name, *args, **kwargs):
    #log.debug(u'Call to deprecated method render_def')
    import adhocracy_client
    return adhocracy_client.render_def(template_name, *args, **kwargs)

def ret_success(message=None, category=None, entity=None, member=None,
                code=200, format='html'):
    return ret_status('OK', message=message, category=category, entity=entity,
                      code=code, format=format, member=member)


def ret_abort(message, category=None, entity=None, member=None, code=500,
              format='html'):
    return ret_status('ABORT', message=message, category=category,
                      entity=entity, code=code, format=format)


def ret_status(type_, message, category=None, entity=None, member=None,
               code=200, format='html'):
    import adhocracy.lib.helpers as h
    response.status_int = code
    if code != 200:
        if format == 'json':
            return ret_json_status(type_, message, code)
        abort(code, message)
    if message:
        if format == 'json':
            return ret_json_status(type_, message, code)
        h.flash(message, category)
    if entity is not None:
        redirect(h.entity_url(entity, format=format, member=member))
    redirect(h.base_url())


def ret_json_status(type_, message, code=200):
    data = {'type': type_,
            'message': message,
            'code': code}
    return render_json(data)


def render_json(data, filename=None, response=response):
    encoding = 'utf-8'  # RFC 4627.3
    response.content_type = 'application/json'
    response.content_encoding = encoding
    if filename is not None:
        response.content_disposition = 'attachment; filename="'\
            + filename.replace('"', '_') + '"'
    return json_dumps(data, encoding=encoding)


def render_png(io, mtime, content_type="image/png", cache_forever=False):
    response.content_type = content_type
    if not cache_forever:
        etag_cache(key=hashlib.sha1(io).hexdigest())
        del response.headers['Cache-Control']
    else:
        response.headers['Cache-Control'] = 'max-age=31556926'
    response.charset = None
    response.last_modified = rfc822.formatdate(timeval=mtime)
    response.content_length = len(io)
    response.pragma = None
    return io
