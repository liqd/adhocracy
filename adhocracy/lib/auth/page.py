from pylons import tmpl_context as c
from authorization import has_permission_bool as has
import poll

def index():
    return has('page.show')
    
def show(p):
    return has('page.show') and not p.is_deleted()

def create():
    return has('page.create')
    
def edit(p):
    if has('instance.admin'):
        return True
    return has('page.edit') and show(p)

def delete(p):
    return has('page.delete') and show(p) and p.is_mutable()
    