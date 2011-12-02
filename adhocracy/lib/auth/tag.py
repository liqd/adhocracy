from pylons import tmpl_context as c
from authorization import has


def index(check):
    check.perm('tag.show')


def show(check, t):
    check.perm('tag.show')


def create(check):
    check.perm('tag.create')


def edit(check, t):
    check.perm('tag.edit')
    show(check, t)


def delete(check, t):
    if has('instance.admin'):
        return
    check.perm('tag.delete')
    show(check, t)
    check.other('not_logged_in', not c.user)
    check.other('tag_creator_is_not_user', t.creator != c.user)
