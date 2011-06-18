from pylons import tmpl_context as c

from adhocracy.lib.auth import poll
from adhocracy.lib.auth.authorization import has


def index():
    return has('proposal.show')


def show(m):
    return has('proposal.show') and not m.is_deleted()


def create():
    if c.instance.frozen:
        return False
    return has('proposal.create')


def edit(m):
    if has('instance.admin'):
        return True
    if not (has('milestone.edit') and show(m)):
        return False
    return False


def delete(m):
    return has('milestone.delete') and show(m)


def is_own(m):
    return c.user and m.creator == c.user

