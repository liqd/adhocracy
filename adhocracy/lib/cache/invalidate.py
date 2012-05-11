import logging
from adhocracy import model
from adhocracy.lib.cache.util import clear_tag

log = logging.getLogger(__name__)


def invalidate_badge(badge):
    log.debug('invalidate_badge %s' % badge)
    clear_tag(badge)


def invalidate_userbadges(userbadges):
    clear_tag(userbadges)
    invalidate_user(userbadges.user)


def invalidate_delegateablebadges(delegateablebadges):
    clear_tag(delegateablebadges)
    invalidate_delegateable(delegateablebadges.delegateable)


def invalidate_user(user):
    clear_tag(user)


def invalidate_text(text):
    clear_tag(text)
    invalidate_page(text.page)


def invalidate_page(page):
    invalidate_delegateable(page)


def invalidate_delegateable(d):
    clear_tag(d)
    for p in d.parents:
        invalidate_delegateable(p)
    if not len(d.parents):
        clear_tag(d.instance)


def invalidate_revision(rev):
    invalidate_comment(rev.comment)


def invalidate_comment(comment):
    clear_tag(comment)
    if comment.reply:
        invalidate_comment(comment.reply)
    invalidate_delegateable(comment.topic)


def invalidate_delegation(delegation):
    invalidate_user(delegation.principal)
    invalidate_user(delegation.agent)


def invalidate_vote(vote):
    clear_tag(vote)
    invalidate_user(vote.user)
    invalidate_poll(vote.poll)


def invalidate_selection(selection):
    if selection is None:
        return
    clear_tag(selection)
    if selection.page:
        invalidate_delegateable(selection.page)
    if selection.proposal:
        invalidate_delegateable(selection.proposal)


def invalidate_poll(poll):
    clear_tag(poll)
    if poll.action == poll.SELECT:
        invalidate_selection(poll.selection)
    elif isinstance(poll.subject, model.Delegateable):
        invalidate_delegateable(poll.subject)
    elif isinstance(poll.subject, model.Comment):
        invalidate_comment(poll.subject)


def invalidate_instance(instance):
    # muharhar cache epic fail
    clear_tag(instance)
    for d in instance.delegateables:
        invalidate_delegateable(d)


def invalidate_tagging(tagging):
    clear_tag(tagging)
    invalidate_delegateable(tagging.delegateable)
