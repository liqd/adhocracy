import rfc822
import hashlib

from pylons import response, tmpl_context as c
from pylons.templating import render_mako, render_mako_def
from pylons.controllers.util import etag_cache
from pylons.controllers.util import abort, redirect

from adhocracy import model
from adhocracy.lib.helpers import json_dumps

import tiles
import text
import auth
import sorting


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


def render(template_name, extra_vars=None, cache_key=None,
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

    page = render_mako(template_name, extra_vars=extra_vars,
                       cache_key=cache_key, cache_type=cache_type,
                       cache_expire=cache_expire)
    return page


def render_def(template_name, def_name, extra_vars=None, cache_key=None,
               cache_type=None, cache_expire=None, **kwargs):
    """
    Signature matches that of pylons actual render_mako_def.
    """
    if not extra_vars:
        extra_vars = {}

    extra_vars.update(tpl_vars())
    extra_vars.update(kwargs)

    return render_mako_def(template_name, def_name,
                           cache_key=cache_key, cache_type=cache_type,
                           cache_expire=cache_expire, **extra_vars)


def ret_success(message=None, category=None, entity=None, code=200,
                format='html'):
    return ret_status('OK', message=message, category=category, entity=entity,
                      code=code, format=format)


def ret_abort(message, category=None, entity=None, code=500, format='html'):
    return ret_status('ABORT', message=message, category=category,
                      entity=entity, code=code, format=format)


def ret_status(type_, message, category=None, entity=None, code=200,
               format='html'):
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
        redirect(h.entity_url(entity, format=format))
    redirect(h.base_url())


def ret_json_status(type_, message, code=200):
    data = {'type': type_,
            'message': message,
            'code': code}
    return render_json(data)


def render_json(data, encoding='utf-8'):
    response.content_type = 'text/javascript'
    response.content_encoding = encoding
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
