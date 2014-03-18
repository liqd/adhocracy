def edit_instance(check):
    check.readonly()
    check.valid_email()
    check.perm('badge.edit_instance')


def edit_global(check):
    check.readonly()
    check.valid_email()
    check.perm('badge.edit_global')


def edit(check, b):
    if b.instance is None:
        edit_global(check)
    else:
        edit_instance(check)


def manage_instance(check):
    check.readonly()
    check.valid_email()
    check.perm('badge.manage_instance')


def manage_global(check):
    check.readonly()
    check.valid_email()
    check.perm('badge.manage_global')


def manage(check, b):
    if b.instance is None:
        manage_global(check)
    else:
        manage_instance(check)
