from authorization import has


def index():
    return has('page.show')


def show(p):
    return has('page.show') and not p.is_deleted()


def create():
    return has('page.create')


def edit(p):
    if not p.is_mutable():
        return False
    if has('instance.admin'):
        return True
    return has('page.edit') and show(p)


def manage(p):
    return has('instance.admin')


def delete(p):
    if not p.is_mutable():
        return False
    return has('page.delete') and show(p)
