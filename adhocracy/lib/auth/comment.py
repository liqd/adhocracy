from pylons import tmpl_context as c
from authorization import has

import poll


def index():
    return has('comment.view')


def show(c):
    return has('comment.view') and not c.is_deleted()


def create():
    return has('comment.create')


def create_on(topic):
    if has('instance.admin'):
        return True
    return create()


def reply(parent):
    return create_on(parent.topic) and not parent.is_deleted()


def is_own(co):
    return c.user and co.creator == c.user


def edit(co):
    if not co.is_mutable():
        return False
    if has('instance.admin'):
        return True
    if not (has('comment.edit') and show(co)):
        return False
    if not (co.wiki or is_own(co)):
        return False
    return True


revert = edit


def delete(co):
    if has('instance.admin'):
        return True
    if edit(co) and is_own(co) and not co.is_edited():
        return True
    return has('comment.delete') and show(co) and not \
        (not co.topic.is_mutable() and co.canonical)


def rate(c):
    return show(c) and c.poll is not None and poll.vote(c.poll)
