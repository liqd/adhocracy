import user


def index(check):
    check.perm('poll.show')


def show(check, p):
    from adhocracy.lib import helpers as h
    check.perm('poll.show')
    check.other('poll_has_ended', p.has_ended())
    check.other('hide_individual_votes', h.poll.hide_individual_votes(p))


def create(check):
    check.readonly()
    check.valid_email()
    check.perm('poll.create')


def edit(check, p):
    check.readonly()
    check.valid_email()
    check.other('polls_can_not_be_edited', True)


def delete(check, p):
    check.readonly()
    check.valid_email()
    check.perm('poll.delete')
    show(check, p)
    check.other('poll_can_not_end', not p.can_end())


def vote(check, p):
    check.readonly()
    check.valid_email()
    check.other('poll_has_ended', p.has_ended())
    check.other('scope_frozen', p.scope.is_frozen())
    check.other('instance_frozen', p.scope.instance.frozen)

    check.other('select_poll_not_mutable',
                (p.action == p.SELECT and p.selection and
                 not p.selection.proposal.is_mutable()))
    user.vote(check)
