from pylons import tmpl_context as c

from adhocracy.lib.auth.authorization import has


# helper functions

def is_own(m):
    return c.user and m.creator == c.user


# authorisation checks

def index(check):
    check.perm('milestone.show')
    check.other('instance_without_milestones', not c.instance.milestones)


def show(check, m):
    check.perm('milestone.show')
    check.other('instance_without_milestones', not c.instance.milestones)
    check.other('milestone_deleted', m.is_deleted())


def create(check):
    check.valid_email()
    check.other('instance_without_milestones', not c.instance.milestones)
    check.perm('milestone.create')


def edit(check, m):
    check.valid_email()
    check.other('instance_without_milestones', not c.instance.milestones)
    if has('instance.admin'):
        return
    check.perm('milestone.edit')
    show(check, m)


def delete(check, m):
    check.valid_email()
    check.perm('milestone.delete')
    show(check, m)
