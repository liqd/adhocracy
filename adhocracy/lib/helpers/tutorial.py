from pylons import session

ALLKEY = 'disable_tutorials'
ONEKEY = 'disable_tutorial_%s'


def show(name):
    if session.get(ALLKEY, False):
        return False
    elif session.get(ONEKEY % name):
        return False
    else:
        return True


def disable(name):
    if name is None:
        session[ALLKEY] = True
    else:
        session[ONEKEY % name] = True
    session.save()


def enable():
    for key in session:
        if key.startswith('disable_tutorial'):
            session[key] = False
    session.save()
