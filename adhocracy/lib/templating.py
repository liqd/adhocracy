import simplejson 
from datetime import datetime
import rfc822

from pylons.templating import render_mako, render_mako_def

import tiles
import util
import text

def tpl_vars():
    vars = dict()
    vars['tiles'] = tiles
    return vars


def render(template_name, extra_vars=None, cache_key=None, 
               cache_type=None, cache_expire=None):
    """
    Signature matches that of pylons actual render_mako. 
    """
    if not extra_vars:
        extra_vars = {}
    
    extra_vars.update(tpl_vars())
    
    return render_mako(template_name, extra_vars=extra_vars, 
                       cache_key=cache_key, cache_type=cache_type,
                       cache_expire=cache_expire)
    
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
        return rfc822.formatdate(float(o.strftime("%s")))
    if hasattr(o, 'to_dict'):
        return o.to_dict()
    raise TypeError("This is not serializable: " + repr(o))

def render_json(data, encoding='utf-8'):
    response.content_type = 'text/javascript'
    response.content_encoding = encoding
    return simplejson.dumps(data, default=_json_entity, 
                            encoding=encoding)
 
    
