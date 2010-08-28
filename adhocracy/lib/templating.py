import simplejson 
from datetime import datetime
import rfc822
import hashlib

from pylons import request, response, tmpl_context as c
from pylons.templating import render_mako, render_mako_def
from pylons.controllers.util import etag_cache
from pylons.controllers.util import abort, redirect

import tiles
import util
import text
import auth
import sorting

def tpl_vars():
    vars = dict()
    vars['tiles'] = tiles
    vars['can'] = auth.can
    vars['diff'] = text.diff
    vars['sorting'] = sorting
    return vars


def render(template_name, extra_vars=None, cache_key=None, 
               cache_type=None, cache_expire=None):
    """
    Signature matches that of pylons actual render_mako. 
    """
    if not extra_vars:
        extra_vars = {}
    
    extra_vars.update(tpl_vars())
    
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

    
def _json_entity(o):
    if isinstance(o, datetime):
        return o.isoformat() + "Z"
    if hasattr(o, 'to_dict'):
        return o.to_dict()
    raise TypeError("This is not serializable: " + repr(o))


def ret_success(message=None, entity=None, code=200, format='html'):
    return ret_status('OK', message=message, entity=entity, 
                      code=code, format=format)

def ret_abort(message, entity=None, code=500, format='html'):
    return ret_status('ABORT', message=message, entity=entity, 
                      code=code, format=format)

def ret_status(type_, message, entity=None, code=200, format='html'):
    import adhocracy.lib.helpers as h
    response.status_int = code
    if code != 200:
        if format == 'json':
            return ret_json_status(type_, message, code)
        abort(code, message)
    if message:
        if format == 'json':
            return ret_json_status(type_, message, code)
        h.flash(message)
    if entity is not None:
        redirect(h.entity_url(entity, format=format))
    redirect(h.base_url(c.instance))    

def ret_json_status(type_, message, code=200):
    data = {'type': type_,
            'message': message,
            'code': code}
    return render_json(data)


def render_json(data, encoding='utf-8'):
    response.content_type = 'text/javascript'
    response.content_encoding = encoding
    return simplejson.dumps(data, default=_json_entity, 
                            encoding=encoding, indent=4)
 

def render_png(io, mtime, content_type="image/png"):
    response.content_type = content_type
    etag_cache(key=hashlib.sha1(io).hexdigest())
    response.charset = None
    response.last_modified = rfc822.formatdate(timeval=mtime)
    del response.headers['Cache-Control']
    response.content_length = len(io)
    response.pragma = None 
    return io

    
