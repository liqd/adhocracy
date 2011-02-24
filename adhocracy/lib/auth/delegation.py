from pylons import tmpl_context as c
from authorization import has
import user


def index():
    return has('delegation.show') and c.instance.allow_delegate


def show(d):
    return (has('delegation.show') and not d.is_revoked() and
            c.instance.allow_delegate)


def create():
    return (has('delegation.create') and user.vote() and
            c.instance.allow_delegate)


def edit(d):
    return False


def delete(d):
    return (has('delegation.delete') and show(d) and
            c.instance.allow_delegate and c.user and d.principal == c.user)
