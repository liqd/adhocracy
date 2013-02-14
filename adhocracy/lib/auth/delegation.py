from pylons import tmpl_context as c
import user


def index(check):
    check.perm('delegation.show')
    check.other('no_instance_allow_delegate', not c.instance.allow_delegate)


def show(check, d):
    check.perm('delegation.show')
    check.other('delegation_revoked', d.is_revoked)
    check.other('no_instance_allow_delegate', not c.instance.allow_delegate)


def create(check):
    check.valid_email()
    check.perm('delegation.create')
    user.vote(check)
    check.other('no_instance_allow_delegate', not c.instance.allow_delegate)


def edit(check, d):
    check.valid_email()
    check.other('cannot_edit_delegations', True)


def delete(check, d):
    check.valid_email()
    check.perm('delegation.delete')
    show(check, d)
    check.other('no_instance_allow_delegate', not c.instance.allow_delegate)
    check.other('not_logged_in', not c.user)
    check.other('delegation_principal_is_not_user', d.principal != c.user)
