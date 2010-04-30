from pylons import tmpl_context as c
from authorization import has_permission_bool as has


def index():
    return has('tag.show')
    
def show(t):
    return has('tag.show') and not t.is_deleted()

def create():
    return has('tag.create')
    
def edit(t):
    return has('tag.edit') and show(t)
    
def delete(t):
    return has('tag.delete') and show(t)
    