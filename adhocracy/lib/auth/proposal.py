from pylons import tmpl_context as c
from authorization import has_permission_bool as has


def index():
    return has('proposal.view')
    
def show(p):
    return has('proposal.view') and not p.is_deleted()

def create():
    return has('proposal.create')
    
def edit(p):
    return has('proposal.edit') and show(p) and p.is_mutable()
    
def delete(p):
    return has('proposal.delete') and show(p) and p.is_mutable()
    
def rate(p):
    return show(p) and has('vote.cast') \
            and p.rate_poll is not None \
            and not p.rate_poll.has_ended()
        
def adopt(p):
    return show(p) and has('poll.create') \
            and p.can_adopt()