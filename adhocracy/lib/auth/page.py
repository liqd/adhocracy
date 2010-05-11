from pylons import tmpl_context as c
from authorization import has_permission_bool as has
from adhocracy.model import Text
import poll

def index():
    return has('page.show')
    
def show(p):
    return has('page.show') and not p.is_deleted()

def create():
    return has('page.create')
    
def edit(p):
    if not p.is_mutable():
        return False
    if has('instance.admin'):
        return True
    return has('page.edit') and show(p)

def variant_edit(p, variant):
    if not edit(p):
        return False
    if not p.has_variants and variant != Text.HEAD:
        return False
    if p.function == p.NORM and variant == Text.HEAD:
        return False
    return True

def delete(p):
    if not p.is_mutable():
        return False
    return has('page.delete') and show(p) and p.is_mutable()
    