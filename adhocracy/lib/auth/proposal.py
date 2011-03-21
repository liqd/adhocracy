from pylons import tmpl_context as c

from adhocracy.lib.auth import poll
from adhocracy.lib.auth.authorization import has


def index():
    return has('proposal.show')


def show(p):
    return has('proposal.show') and not p.is_deleted()


def create():
    if c.instance.frozen:
        return False
    return has('proposal.create')


def edit(p):
    if not p.is_mutable():
        return False
    if has('instance.admin'):
        return True
    if not (has('proposal.edit') and show(p)):
        return False
    if (p.description.head.wiki or is_own(p)):
        return True
    return False


def delete(p):
    return has('proposal.delete') and show(p) and p.is_mutable()


def rate(p):
    return show(p) and p.rate_poll is not None and poll.vote(p.rate_poll)


def adopt(p):
    return show(p) and poll.create() and p.can_adopt()


def is_own(p):
    return c.user and p.creator == c.user
