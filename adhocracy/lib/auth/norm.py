from pylons import tmpl_context as c
from authorization import has
from adhocracy.model import Text
import page
import variant

index = page.index
show = page.show


def create(variant=Text.HEAD):
    return has('instance.admin') and page.create()


def edit(n, variant=Text.HEAD):
    return variant.edit(n, variant)


def delete(n):
    return False