from authorization import has


def index():
    return has('watch.show')


def show(w):
    return has('watch.show') and not w.is_deleted()


def create():
    return has('watch.create')


def delete(w):
    return has('watch.delete') and show(w)
