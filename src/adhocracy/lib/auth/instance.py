from pylons import tmpl_context as c, app_globals as g
from authorization import has
from adhocracy.lib.auth.authorization import NOT_LOGGED_IN


def index(check):
    check.other('is_single_instance', g.single_instance)
    check.perm('instance.index')


def show(check, i):
    check.perm('instance.show')
    check.other('instance_deleted', i.is_deleted())


def create(check):
    check.valid_email()
    check.other('is_single_instance', g.single_instance)
    check.perm('instance.create')


def edit(check, i):
    check.perm('instance.admin')
    show(check, i)

admin = edit


def any_admin(check):
    if has('global.admin'):
        return
    check.perm('instance.admin')


def authenticated_edit(check, instance):
    '''
    Edit allowed only in authenticated instances
    '''
    check.other('is_not_authenticated', not instance.is_authenticated)
    edit(check, instance)


def delete(check, i):
    check.other('is_single_instance', g.single_instance)
    check.perm('global.admin')
    show(check, i)


def join(check, i):
    check.other('instance_frozen', i.frozen)
    show(check, i)
    check.perm('instance.join')
    check.other(NOT_LOGGED_IN, not c.user)
    if c.user:
        check.other('user_is_member', c.user.is_member(i))


def leave(check, i):
    check.other('is_single_instance', g.single_instance)
    check.other('instance_frozen', i.frozen)
    show(check, i)
    check.perm('instance.leave')
    check.other('not_logged_in', not c.user)
    if c.user:
        check.other('user_is_no_member', not c.user.is_member(i))
        check.other('user_is_instance_creator', c.user == i.creator)
