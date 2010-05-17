from pylons import tmpl_context as c
from authorization import has_permission_bool as has
import user

def index():
    return has('poll.show')
    
def show(p):
    return has('poll.show') and not p.has_ended()

def create():
    return has('poll.create')
    
def edit(p):
    return False
    
def delete(p):
    return has('poll.delete') and show(p) and p.can_end()

def vote(p):
    if p.action == p.SELECT and not p.selection.proposal.is_mutable():
        return False
    return show(p) and user.vote() and not p.has_ended()