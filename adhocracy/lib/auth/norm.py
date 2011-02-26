from pylons import tmpl_context as c
from authorization import has
from adhocracy.model import Text
import page
import variant as _variant

index = page.index
show = page.show


def create(variant=Text.HEAD):
    return has('instance.admin') and page.create() and c.instance.use_norms

def propose():
    if has('instance.admin') and c.instance.use_norms:
        return True
    if not c.instance.allow_propose: 
        return False
    return has('page.edit')

def edit(page, variant=Text.HEAD):
    if not page.instance.use_norms:
        return False
    return _variant.edit(page, variant)

def delete(n):
    return False
