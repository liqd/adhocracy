from pylons import tmpl_context as c
from authorization import has_permission_bool as has
import poll

def index():
    return has('instance.index')
    
def show(i):
    return has('instance.show') and not i.is_deleted()

def create():
    return has('instance.create')
    
def edit(i):
    return has('instance.admin') and show(i)
    
admin = edit    
    
def delete(i):
    return has('global.admin') and show(i)
    
def join(i):
    return show(i) and has('instance.join') and c.user and \
        not c.user.is_member(i)

def leave(i):
    return show(i) and has('instance.leave') and c.user and \
        c.user.is_member(i) and not c.user == i.creator
    