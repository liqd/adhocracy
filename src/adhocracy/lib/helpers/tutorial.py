from paste.deploy.converters import asbool
from pylons import config
from pylons import session

from adhocracy.model import meta

ALLKEY = 'disable_tutorials'
ONEKEY = 'disable_tutorial_%s'


def show(name, user):
    if not asbool(config.get('adhocracy.show_tutorials', 'true')):
        return False

    if user is not None and user.no_help:
        return False
    if session.get(ALLKEY, False):
        return False
    elif session.get(ONEKEY % name):
        return False
    else:
        return True


def disable(name, user):
    if name is None:
        if user is None:
            session[ALLKEY] = True
        else:
            user.no_help = True
            meta.Session.commit()
    else:
        session[ONEKEY % name] = True
    session.save()


def enable():
    for key in session:
        if key.startswith('disable_tutorial'):
            session[key] = False
    session.save()
