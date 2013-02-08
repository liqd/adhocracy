def index(check):
    check.perm('watch.show')


def show(check, w):
    check.perm('watch.show')
    check.other('watch_is_deleted', w.is_deleted())


def create(check):
    check.perm('watch.create')


def delete(check, w):
    check.perm('watch.delete')
    show(check, w)
