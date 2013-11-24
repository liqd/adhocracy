from authorization import has
import proposal


def index(check, p):
    return proposal.index(check)


def show(check, s):
    check.perm('proposal.show')
    check.other('selection_is_deleted', s.is_deleted())


def create(check, p):
    check.readonly()
    check.valid_email()
    check.other('proposal_not_mutable', not p.is_mutable())
    if has('instance.admin'):
        return
    check.perm('proposal.edit')
    show(check, p)


def edit(check, s):
    check.readonly()
    check.valid_email()
    check.other('selections_can_not_be_edited', False)
    check.other('proposal_not_mutable',
                s.proposal and not s.proposal.is_mutable())


def delete(check, s):
    check.valid_email()
    proposal.delete(check, s.proposal)
    show(check, s)
