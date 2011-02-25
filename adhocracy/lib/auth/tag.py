from pylons import tmpl_context as c
from authorization import has


def index():
    return has('tag.show')


def show(t):
    return has('tag.show')


def create():
    return has('tag.create')


def edit(t):
    return has('tag.edit') and show(t)


def delete(t):
    if has('instance.admin'):
        return True
    return has('tag.delete') and show(t) and c.user and t.creator == c.user
