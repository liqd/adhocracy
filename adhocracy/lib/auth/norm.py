from pylons import tmpl_context as c
from authorization import has_permission_bool as has
from adhocracy.model import Text
import page

index = page.index
show = page.create 
create = page.create


def edit(n, variant):
    if variant == Text.HEAD and not has('instance.admin'):
        return False
    return page.edit(n)


def delete(n):
    return False