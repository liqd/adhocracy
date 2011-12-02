from adhocracy.lib.auth.authorization import has
import user


def index(check):
    check.perm('poll.show')


def show(check, p):
    check.perm('poll.show')
    check.other('poll_has_ended', p.has_ended())


def create(check):
    check.perm('poll.create')


def edit(check, p):
    check.other('polls_can_not_be_edited', True)


def delete(check, p):
    check.perm('poll.delete')
    show(check, p)
    check.other('poll_can_not_end', not p.can_end())


def vote(check, p):
    check.other('select_poll_not_mutable',
            p.action == p.SELECT and not p.selection.proposal.is_mutable())
    show(check, p)
    user.vote(check)
    check.other('poll_has_ended', p.has_ended())
