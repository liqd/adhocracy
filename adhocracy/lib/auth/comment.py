from pylons import tmpl_context as c
from authorization import has

import poll


# helper functions

def is_own(co):
    return c.user and co.creator == c.user


# authorisation checks

def index(check):
    check.perm('comment.view')


def show(check, co):
    check.perm('comment.view')
    check.other('comment_is_deleted', co.is_deleted())


def create(check):
    check.valid_email()
    check.perm('comment.create')


def create_on(check, topic):
    check.valid_email()
    if has('instance.admin'):
        return
    check.other('topic_instance_frozen', topic.instance.frozen)
    create(check)


def reply(check, parent):
    check.valid_email()
    create_on(check, parent.topic)
    check.other('parent_deleted', parent.is_deleted())


def edit(check, co):
    check.valid_email()
    check.other('comment_not_mutable', not co.is_mutable())
    if has('instance.admin'):
        return
    check.other('comment_topic_instance_frozen', co.topic.instance.frozen)
    check.perm('comment.edit')
    show(check, co)
    check.other('comment_is_not_wiki_or_own', not (co.wiki or is_own(co)))


revert = edit


def delete(check, co):
    check.valid_email()
    if has('instance.admin'):
        return
    check.other('comment_topic_instance_frozen', co.topic.instance.frozen)
    edit(check, co)
    check.other('comment_is_not_own', not is_own(co))
    check.other('comment_is_edited', co.is_edited())
    check.perm('comment.delete')
    show(check, co)
    check.other('comment_not_mutable', not co.topic.is_mutable())


def rate(check, co):
    check.valid_email()
    check.other('comment_topic_instance_frozen', co.topic.instance.frozen)
    show(check, co)
    check.other('comment_poll_is_none', co.poll is not None)
    poll.vote(check, co.poll)
