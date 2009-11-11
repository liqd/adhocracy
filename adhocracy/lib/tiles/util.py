
from pylons import request, response, session, tmpl_context as c

from .. import helpers as h
from .. import authorization as auth
from .. import karma

class BaseTile(object):
    
    @classmethod
    def lack_karma(cls, perm):
        if h.has_permission(perm) and \
                not karma.threshold.has(c.user, perm):
            return karma.threshold.message(perm)
        return None
    
    @classmethod
    def prop_lack_karma(cls, perm):
        return lambda self: BaseTile.lack_karma(perm)
    
    @classmethod
    def prop_has_perm(cls, perm):
        return lambda self: h.has_permission(perm)



def render_tile(template_name, def_name, tile, **kwargs):
    from .. import templating
    return templating.render_def(template_name, def_name, tile=tile, **kwargs)