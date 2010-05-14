from pylons import tmpl_context as c
from authorization import has_permission_bool as has
from adhocracy.model import Text
import page

index = page.index
show = page.show


def create(variant=Text.HEAD):
    return has('instance.admin') and page.create()


def edit(n, variant=Text.HEAD):
    if variant == Text.HEAD and not has('instance.admin'):
        return False
    return page.edit(n)


def delete(n):
    return False