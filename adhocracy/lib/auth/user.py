from pylons import tmpl_context as c
from authorization import has_permission_bool as has


def index():
    return has('user.view')
    
def show(u):
    return has('user.view') and not u.is_deleted()

def create():
    return not c.user #has('user.create')
    
def edit(u):
    if manage(u):
        return True
    return has('user.edit') and show(u) and u == c.user
    
def manage(u):
    return has('user.manage')
    
def supervise(u):
    if (not c.instance) or (not u.is_member(c.instance)):
        return False
    return manage(u) or has('instance.admin')
    
def delete(p):
    return False
    
def vote():
    return c.instance and c.user and has('vote.cast')
