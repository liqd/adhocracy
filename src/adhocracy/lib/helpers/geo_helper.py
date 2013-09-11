from copy import copy
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

    imageLayers = copy(config.get_json('adhocracy.geo.image_layers'))

    if c.instance and config.get_bool('adhocracy.geo.instance_overwrites'):
        imageLayers.extend(config.get_json(
            'adhocracy.geo.image_layers.' + c.instance.key,
            default=[]))
        fallbackBounds = config.get_list(
            'adhocracy.geo.fallback_bounds.' + c.instance.key, cast=float)
        restrictedBounds = config.get_list(
            'adhocracy.geo.restricted_bounds.' + c.instance.key, cast=float)
    else:
        fallbackBounds = None
        restrictedBounds = None

    if fallbackBounds is None:
        fallbackBounds = config.get_list('adhocracy.geo.fallback_bounds',
                                         cast=float)
    if restrictedBounds is None:
        restrictedBounds = config.get_list('adhocracy.geo.restricted_bounds',
                                           cast=float)

    return to_json(
        restrictedBounds=restrictedBounds,
        fallbackBounds=fallbackBounds,
        imageLayers=imageLayers,
        **kwargs)
