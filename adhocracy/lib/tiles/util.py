import logging 

from pylons import tmpl_context as c

from .. import helpers as h
from .. import karma
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
    if cached:
        @memoize('tile_cache' + template_name + def_name)
        def _cached(**kwargs):
            return render()
        rendered = _cached(**kwargs)
    else:
        rendered = render()
    log.debug("Rendering tile %s:%s took %sms" % (template_name, def_name, (time()-begin_time)*1000))
    return rendered