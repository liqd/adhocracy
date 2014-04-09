""" Change UI depending on user badges """

import collections

from paste.deploy.converters import asbool
from pylons import config
from pylons.i18n import _


def behavior_enabled(config=config):
    return asbool(config.get('adhocracy.enable_behavior', 'False'))


def get_behavior(user, key):
    assert key in ['proposal_sort_order']

    if not behavior_enabled():
        return None

    if user is None:
        return None

    propname = 'behavior_' + key
    for b in user.badges:
        v = getattr(b, propname)
        if v is not None:
            return v
    return None
