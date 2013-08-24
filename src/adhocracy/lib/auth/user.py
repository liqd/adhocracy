from paste.deploy.converters import asbool
from pylons import tmpl_context as c, config
from adhocracy.lib.auth.authorization import has
from adhocracy.lib.auth.authorization import NOT_LOGGED_IN


def index(check):
    check.perm('user.view')


def show(check, u):
    check.perm('user.view')
    check.other('user_deleted', u.is_deleted())


def create(check):
    check.other('user_logged_in', c.user is not None)


def edit(check, u):
    if has('user.manage'):
        return
    show(check, u)
    check.other('user_not_self', u != c.user)
    check.other(NOT_LOGGED_IN, not c.user)


def manage(check, u):
    check.perm('user.manage')


def message(check, u):
    check.perm('user.message')
    check.other('user_is_self', u == c.user)
    check.other('user_without_email', u.email is None)
    check.other('email_not_activated', not u.is_email_activated())
    if c.instance is not None:
        check.other('no_member_in_instance', not u.is_member(c.instance))


def supervise(check, u):
    check.other('not_in_instance', not c.instance)
    check.other('no_member_in_instance', not u.is_member(c.instance))
    check.other('not_user.manage_or_instance.admin',
                not (has('user.manage') or has('instance.admin')))


def show_dashboard(check, u):
    show(check, u)
    check.other('user_not_self', u != c.user)


show_watchlist = show_dashboard


def delete(check, u):
    edit(check, u)
    allowed = asbool(config.get('adhocracy.self_deletion_allowed', 'true'))
    check.other('self_deletion_allowed', not allowed)


def vote(check):
    check.other('vote_prohibited', has('vote.prohibit'))
    check.other('not_in_instance', not c.instance)
    check.other(NOT_LOGGED_IN, not c.user)
    check.perm('vote.cast')
