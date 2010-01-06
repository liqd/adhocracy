import logging 

from pylons import tmpl_context as c

from .. import helpers as h
from .. import karma
#from ..cache import memoize

log = logging.getLogger(__name__)

class BaseTile(object):
    
    @classmethod
    def prop_has_perm(cls, perm):
        return lambda self: h.has_permission(perm)


from time import time

def render_tile(template_name, def_name, tile, **kwargs):
    from .. import templating 
    begin_time = time()
    rendered = templating.render_def(template_name, def_name, tile=tile, **kwargs)
    log.debug("Rendering tile %s:%s took %sms" % (template_name, def_name, (time()-begin_time)*1000))
    return rendered