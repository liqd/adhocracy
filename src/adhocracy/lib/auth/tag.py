from pylons import tmpl_context as c
from authorization import has
from adhocracy.lib.auth.authorization import NOT_LOGGED_IN


def index(check):
    check.perm('tag.show')


def show(check, t):
    check.perm('tag.show')


def create(check):
    check.valid_email()
    check.perm('tag.create')


def edit(check, t):
    check.valid_email()
    check.perm('tag.edit')
    show(check, t)


def delete(check, t):
    check.valid_email()
    if has('instance.admin'):
        return
    check.perm('tag.delete')
    show(check, t)
    check.other(NOT_LOGGED_IN, not c.user)
    check.other('tag_creator_is_not_user', t.creator != c.user)
