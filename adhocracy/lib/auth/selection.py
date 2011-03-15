from authorization import has
import proposal


def index(p):
    return proposal.index()


def show(s):
    return has('proposal.show') and not s.is_deleted()


def create(p):
    if not p.is_mutable():
        return False
    if has('instance.admin'):
        return True
    if not (has('proposal.edit') and show(p)):
        return False
    #if (p.description.head.wiki or is_own(p)):
    #    return True
    return True

def edit(s):
    return False


def delete(s):
    return proposal.delete(s.proposal) and show(s)
