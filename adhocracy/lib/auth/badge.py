def edit_instance(check):
    check.perm('instance.admin')


def edit_global(check):
    check.perm('global.admin')


def manage_instance(check):
    check.perm('instance.admin')


def manage_global(check):
    check.perm('global.admin')
