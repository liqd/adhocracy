from pylons import tmpl_context as c, g
from authorization import has
import poll

def index():
    if g.single_instance:
        return False
    return has('instance.index')
    
def show(i):
    return has('instance.show') and not i.is_deleted()

def create():
    if g.single_instance:
        return False
    return has('instance.create')
    
def edit(i):
    return has('instance.admin') and show(i)
    
admin = edit    
    
def delete(i):
    if g.single_instance:
        return False
    return has('global.admin') and show(i)
    
def join(i):
    return show(i) and has('instance.join') and c.user and \
        not c.user.is_member(i)

def leave(i):
    if g.single_instance:
        return False
    return show(i) and has('instance.leave') and c.user and \
        c.user.is_member(i) and not c.user == i.creator
    