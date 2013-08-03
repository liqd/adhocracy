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
