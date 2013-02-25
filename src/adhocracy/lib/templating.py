import rfc822
import hashlib
import logging

from pylons import response
import pylons.templating
from pylons.controllers.util import etag_cache
from pylons.controllers.util import abort, redirect

from adhocracy import model
from adhocracy.lib.helpers import json_dumps

import tiles
import text
import auth
import sorting

log = logging.getLogger(__name__)


def tpl_vars():
    vars = dict()
    import adhocracy.lib
    vars['tiles'] = tiles
    vars['lib'] = adhocracy.lib
    vars['can'] = auth.can
    vars['check'] = auth.check
    vars['diff'] = text.diff
    vars['sorting'] = sorting
    vars['model'] = model
    return vars

_legacy = object()
def render(template_name, data=_legacy, overlay=False):
    """ If overlay is True, the template will be rendered in a minimal template
        containing only the main content markup of the site."""

    if data is _legacy:
        # log.debug(u'Legacy call to render() - missing data')
        data = {}

    return render_mako(template_name, data, overlay=overlay)


def render_mako(template_name, data, extra_vars=None, cache_key=None,
           cache_type=None, cache_expire=None, overlay=False):
    """
    Signature matches that of pylons actual render_mako. Except
    for the *overlay* parameter. If it is *True*, the template will
    be rendered in a minimal template containing only the main content
    markup of the site.
    """
    if not extra_vars:
        extra_vars = {}

    extra_vars.update(tpl_vars())

    if overlay:
        extra_vars['root_template'] = '/overlay.html'

    for k,v in data.items():
        setattr(pylons.tmpl_context, k, v)

    page = pylons.templating.render_mako(template_name, extra_vars=extra_vars,
                       cache_key=cache_key, cache_type=cache_type,
                       cache_expire=cache_expire)
    return page


def render_def(template_name, def_name, extra_vars=None, cache_key=None,
               cache_type=None, cache_expire=None, **kwargs):
    """
    Signature matches that of pylons actual render_mako_def.
    """
    # log.debug(u'Call to deprecated (Mako-specific) method render_def -'
    #           u'call render(template_name, data, only_fragment=True) instead')
    if not extra_vars:
        extra_vars = {}

    extra_vars.update(tpl_vars())
    extra_vars.update(kwargs)

    return pylons.templating.render_mako_def(template_name, def_name,
                           cache_key=cache_key, cache_type=cache_type,
                           cache_expire=cache_expire, **extra_vars)


def ret_success(message=None, category=None, entity=None, member=None,
                code=200, format='html', force_path=None):
    return ret_status('OK', message=message, category=category, entity=entity,
                      code=code, format=format, member=member,
                      force_path=force_path)


def ret_abort(message, category=None, entity=None, member=None, code=500,
              format='html', force_path=None):
    return ret_status('ABORT', message=message, category=category,
                      entity=entity, code=code, format=format,
                      force_path=force_path)


def ret_status(type_, message, category=None, entity=None, member=None,
               code=200, format='html', force_path=None):
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
    if force_path is not None:
        redirect(force_path)
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
