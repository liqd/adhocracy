from pylons import tmpl_context as c

from adhocracy import config
from adhocracy.lib.auth.authorization import has
from adhocracy.lib.auth.authorization import NOT_LOGGED_IN


def is_not_demo(check, u):
    if u is not None:
        demo_users = config.get_list('adhocracy.demo_users')
        check.other('demo_user', u.user_name in demo_users)


def index(check):
    check.perm('user.view')


def show(check, u):
    check.perm('user.view')
    check.other('user_deleted', u.is_deleted())


def create(check):
    check.readonly()
    check.other('user_logged_in', c.user is not None)


def edit(check, u):
    check.readonly()
    if has('user.manage'):
        return
    show(check, u)
    check.other('user_not_self', u != c.user)
    check.other(NOT_LOGGED_IN, not c.user)
    is_not_demo(check, c.user)


def manage(check, u=None):
    """ Manage users on installation level """
    check.readonly()
    check.perm('user.manage')


def message(check, u):
    check.readonly()
    check.perm('user.message')
    check.other('user_is_self', u == c.user)
    if c.instance is not None:
        check.other('no_member_in_instance', not u.is_member(c.instance))


def badge(check, u):
    check.readonly()
    check.perm('user.badge')


def supervise(check, u=None):
    """ Supervise users on instance level """
    check.readonly()
    check.other('not_in_instance', not c.instance)
    if u is not None:
        check.other('no_member_in_instance', not u.is_member(c.instance))
    check.other('not_user.manage_or_instance.admin',
                not (has('user.manage') or has('instance.admin')))


def show_dashboard(check, u):
    show(check, u)
    check.other('user_not_self', u != c.user)


show_watchlist = show_dashboard


def delete(check, u):
    edit(check, u)
    allowed = config.get_bool('adhocracy.self_deletion_allowed', True)
    check.other('self_deletion_allowed', not allowed)


def vote(check):
    check.readonly()
    check.other('vote_prohibited', has('vote.prohibit'))
    check.other('not_in_instance', not c.instance)
    check.other(NOT_LOGGED_IN, not c.user)
    check.perm('vote.cast')
