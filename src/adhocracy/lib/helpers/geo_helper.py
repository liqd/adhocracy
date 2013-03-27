from pylons import config
from pylons import tmpl_context as c
from paste.deploy.converters import asbool


def use_maps():
    return c.instance.use_maps


def use_proposal_geotags():
    return use_maps() and asbool(config.get('adhocracy.proposal_geotags'))


def use_page_geotags():
    return use_maps() and asbool(config.get('adhocracy.page_geotags'))
