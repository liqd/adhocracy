def edit_instance(check):
    check.valid_email()
    check.perm('instance.admin')


def edit_global(check):
    check.valid_email()
    check.perm('global.admin')


def manage_instance(check):
    check.valid_email()
    check.perm('instance.admin')


def manage_global(check):
    check.valid_email()
    check.perm('global.admin')
