from pylons import session

KEY = 'disable_tutorials'

def show():
    if session.get(KEY, False):
        return False
    else:
        return True


def disable():
    session[KEY] = True
    session.save()


def enable():
    session[KEY] = False
    session.save()
