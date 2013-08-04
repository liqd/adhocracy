from pylons import tmpl_context as c
from adhocracy import config


def use_maps():
    if c.instance is None:
        return True
    else:
        return c.instance.use_maps


def use_proposal_geotags():
    return use_maps() and config.get_bool('adhocracy.proposal_geotags')


def use_page_geotags():
    return use_maps() and config.get_bool('adhocracy.page_geotags')


def map_config(**kwargs):
    from adhocracy.lib.helpers import to_json
    return to_json(
        restrictedBounds=config.get_list('adhocracy.geo.restricted_bounds',
                                         cast=float),
        fallbackBounds=config.get_list('adhocracy.geo.fallback_bounds',
                                       cast=float),
        imageLayers=config.get_json('adhocracy.geo.image_layers'),
        **kwargs)
