from pylons import tmpl_context as c
from authorization import has
from adhocracy.model import Text
import page
import variant as _variant

index = page.index
show = page.show


def create(check, variant=Text.HEAD):
    check.perm('instance.admin')
    page.create(check)
    check.other('instance_without_norms', not c.instance.use_norms)
    check.other('instance_frozen', c.instance.frozen)


def propose(check):
    check.other('instance_without_norms')
    if has('instance.admin'):
        return
    check.other('no_instance_allow_propose', not c.instance.allow_propose)
    check.other('instance_frozen', i.frozen)
    check.perm('page.edit')


def edit(check, page, variant=Text.HEAD):
    check.other('page_instance_without_norms', not page.instance.use_norms)
    _variant.edit(check, page, variant)


def delete(check, n):
    check.other('norms_cannot_be_deleted', True)
