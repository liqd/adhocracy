import logging 

from pylons import tmpl_context as c, config

from .. import helpers as h
from ..cache import memoize

log = logging.getLogger(__name__)

class BaseTile(object):
    
    @classmethod
    def prop_has_perm(cls, perm):
        return lambda self: h.has_permission(perm)


from time import time

def render_tile(template_name, def_name, tile, cached=False, **kwargs):
    from .. import templating 
    begin_time = time()
    render = lambda: templating.render_def(template_name, def_name, tile=tile, **kwargs)
    rendered = ""
    if cached and config.get('adhocracy.cache_tiles', True):
        @memoize('tile_cache' + template_name + def_name, 84600/4)
        def _cached(**kwargs):
            return render()
        rendered = _cached(locale=c.locale, **kwargs)
    else:
        rendered = render()
    #log.debug("Rendering tile %s:%s took %sms" % (template_name, def_name, (time()-begin_time)*1000))
    return rendered