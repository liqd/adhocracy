from authorization import has
from adhocracy.model import Text

import page


def edit(check, p, variant):
    check.valid_email()
    check.other('instance_without_norms', not p.instance.use_norms)
    check.other('instance_frozen', p.instance.frozen)
    check.other('variant_is_none', variant is None)
    if has('instance.admin'):
        return
    page.edit(check, p)

    check.other('page_has_no_variants_and_variant_is_not_head',
                not p.has_variants and variant != Text.HEAD)
    check.other('page_function_is_norm_and_variant_is_head',
                p.function == p.NORM and variant == Text.HEAD)


def delete(check, p, variant):
    check.valid_email()
    check.other('variant_is_none', variant is None)
    check.other('variant_is_head', variant == Text.HEAD)
    if has('instance.admin'):
        return
    page.delete(check, p)
