from authorization import has


def index(check):
    check.perm('page.show')


def show(check, p):
    check.perm('page.show')
    check.other('page_deleted', p.is_deleted())


def create(check):
    check.perm('page.create')


def edit(check, p):
    check.other('page_not_mutable', not p.is_mutable())
    if has('instance.admin'):
        return
    check.perm('page.edit')
    show(check, p)


def manage(check, p):
    check.perm('instance.admin')


def delete(check, p):
    check.other('page_not_mutable', not p.is_mutable())
    check.perm('page.delete')
    show(check, p)


def delete_history(check, p):
    check.perm('page.delete_history')
