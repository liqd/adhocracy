from pylons import tmpl_context as c
from authorization import has
import poll

def index():
    return has('proposal.show')
    
def show(p):
    return has('proposal.show') and not p.is_deleted()

def create():
    return has('proposal.create')
    
def edit(p):
    return has('proposal.edit') and show(p) and p.is_mutable()
    
def delete(p):
    return has('proposal.delete') and show(p) and p.is_mutable()
    
def rate(p):
    return show(p) and p.rate_poll is not None and poll.vote(p.rate_poll)
            
def adopt(p):
    return show(p) and poll.create() and p.can_adopt()