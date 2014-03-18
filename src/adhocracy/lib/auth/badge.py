def edit_instance(check):
    check.readonly()
    check.valid_email()
    check.perm('badge.edit_instance')


def edit_global(check):
    check.readonly()
    check.valid_email()
    check.perm('badge.edit_global')


def manage_instance(check):
    check.readonly()
    check.valid_email()
    check.perm('badge.manage_instance')


def manage_global(check):
    check.readonly()
    check.valid_email()
    check.perm('badge.manage_global')
