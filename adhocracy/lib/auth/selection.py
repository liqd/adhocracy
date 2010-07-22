from pylons import tmpl_context as c
from authorization import has
import proposal


def index(p):
    return proposal.index()
    
def show(s):
    return has('proposal.show') and not s.is_deleted()

def create(p):
    if not p.is_mutable():
        return False
    return proposal.edit(p)
    
def edit(s):
    return False
    
def delete(s):
    return proposal.delete(s.proposal) and show(s)