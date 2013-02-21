import logging
from time import time

from pylons import tmpl_context as c, config

from adhocracy.lib.cache import memoize

log = logging.getLogger(__name__)


class BaseTile(object):
    '''
    Base class for tiles
    '''


def render_tile(template_name, def_name, tile, cached=False, **kwargs):
    from adhocracy.lib import templating
    begin_time = time()

    def render():
        return templating.render_def(template_name, def_name,
                                     tile=tile, **kwargs)
    rendered = ""
    if cached and config.get('adhocracy.cache_tiles', True):
        @memoize('tile_cache' + template_name + def_name, 86400 / 4)
        def _cached(**kwargs):
            return render()
        rendered = _cached(locale=c.locale, **kwargs)
    else:
        rendered = render()

    if False:
        log.debug("Rendering tile %s:%s took %sms" % (
            template_name, def_name, (time() - begin_time) * 1000))

    return rendered
