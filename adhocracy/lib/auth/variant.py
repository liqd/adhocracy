from pylons import tmpl_context as c
from authorization import has
from adhocracy.model import Text

def edit(p, variant):
    if not p.instance.use_norms:
        return False
    if variant is None: 
        return False
    if has('instance.admin'): 
        return True
    if not edit(p): 
        return False
    if not p.has_variants and variant != Text.HEAD:
        return False
    if p.function == p.NORM and variant == Text.HEAD:
        return False
    return True
    
def delete(p, variant):
    if variant is None: 
        return False
    if variant == Text.HEAD:
        return False
    if has('instance.admin'): 
        return True
    return delete(p)