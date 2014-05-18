# coding: utf-8
import cgi
import logging

from pylons.i18n import _

from adhocracy import model
from adhocracy.lib import helpers as h
from adhocracy.lib.event.types import (S_INSTANCE, S_VOTE, S_DELEGATION_IN,
    S_DELEGATION_OUT, S_PROPOSAL, S_AMENDMENT, S_COMMENT, S_PAGE, S_BADGE,
    S_MESSAGE)

log = logging.getLogger(__name__)
DT_FORMAT = "%Y%m%d%H%M%S"


class ObjectFormatter(object):

    def unicode(self, value):
        return value

    def html(self, value):
        return value


class DelegateableFormatter(ObjectFormatter):

    def unicode(self, delegateable):
        return delegateable.full_title

    def html(self, delegateable):
        return h.delegateable.link(delegateable)


class ProposalFormatter(DelegateableFormatter):
    pass


class PageFormatter(DelegateableFormatter):
    pass


class PollFormatter(ObjectFormatter):

    SELECT_PATTERN = lambda s, v, p: _("variant %(variant)s of %(page)s") % \
        {'variant': v,
         'page': p}

    def _get_formatter(self, poll):
        if isinstance(poll.subject, model.Comment):
            return CommentFormatter()
        if isinstance(poll.subject, model.Delegateable):
            return DelegateableFormatter()
        else:
            return unicode(poll.subject)

    def unicode(self, poll):
        if poll.action == poll.SELECT and poll.selection:
            text = poll.selection.page.variant_head(poll.variant)
            return self.SELECT_PATTERN(text.variant_name,
                                       poll.selection.page.title)
        else:
            fmt = self._get_formatter(poll)
            return fmt.unicode(poll.subject)

    def html(self, poll):
        if poll.action == poll.SELECT:
            text = poll.selection.page.variant_head(poll.variant)
            variant_link = "<a href='%s'>%s</a>" % (h.text.url(text),
                                                    text.variant_html)
            page_link = h.page.link(poll.selection.page)
            return self.SELECT_PATTERN(variant_link, page_link)
        else:
            fmt = self._get_formatter(poll)
            return fmt.html(poll.subject)


class InstanceFormatter(ObjectFormatter):

    def unicode(self, instance):
        return instance.label

    def html(self, instance):
        return u"<a class='event_instance' href='%s'>%s</a>" % (
            h.entity_url(instance),
            instance.label)


class UserFormatter(ObjectFormatter):

    def unicode(self, user):
        return user.name

    def html(self, user):
        return h.user.link(user)


class GroupFormatter(ObjectFormatter):

    def unicode(self, group):
        return _(group.group_name)

    def html(self, group):
        return self.unicode(group)


class VoteFormatter(ObjectFormatter):

    def unicode(self, vote):
        return {1: _("is for"),
                0: _("abstains on"),
                -1: _("is against")}[vote.orientation]

    def html(self, value):
        return {
            1: u'%s <span class="pro">%s ✓</span>' % (
                _(u'is'), _(u'for')),
            0: _(u'abstains on'),
            -1: u'%s <span class="con">%s ×</span>' % (
                _(u'is'), _(u'against')),
        }[value.orientation]


class CommentFormatter(ObjectFormatter):

    def unicode(self, comment):
        if h.comment.wording():
            return _("comment on %s" % comment.topic.title)
        else:
            return _("argument on %s" % comment.topic.title)

    def html(self, comment):
        if comment.delete_time:
            return self.unicode(comment)
        return "<a href='%s'>%s</a>" % (h.entity_url(comment),
                                        cgi.escape(self.unicode(comment)))


class MessageFormatter(ObjectFormatter):

    def unicode(self, message):
        return message.subject

    def html(self, message):
        return '<a href="%s">%s</a>' % (h.entity_url(message),
                                        cgi.escape(self.unicode(message)))


class FormattedEvent(object):

    FORMATTERS = {model.Vote: VoteFormatter(),
                  model.Group: GroupFormatter(),
                  model.User: UserFormatter(),
                  model.Instance: InstanceFormatter(),
                  model.Proposal: ProposalFormatter(),
                  model.Poll: PollFormatter(),
                  model.Page: PageFormatter(),
                  model.Comment: CommentFormatter(),
                  model.Message: MessageFormatter()}

    def __init__(self, event, decoder):
        self.event = event
        self.decoder = decoder

    def __getitem__(self, item):
        try:
            value = self.event[item]
            for cls in self.FORMATTERS.keys():
                if isinstance(value, cls):
                    return self.decoder(self.FORMATTERS[cls], value)
            return value
        except AttributeError, ae:
            log.exception(ae)
            return _("(Undefined)")


def _format(event, decoder, msg=None):
    if not event.event:
        return _("(Undefined)")
    fe = FormattedEvent(event, decoder)
    if msg is None:
        msg = event.event.event_msg()
    return msg % fe


def as_unicode(event, msg=None):
    return _format(event, lambda f, value: f.unicode(value), msg)


def as_html(event, msg=None):
    return _format(event, lambda f, value: f.html(value), msg)


def as_icon(event, classes=''):
    if event.event.code in S_INSTANCE:
        icon = 'event-instance'
    elif event.event.code in S_PAGE:
        icon = 'event-page'
    elif event.event.code in S_COMMENT:
        icon = 'event-comment'
    elif event.event.code in S_PROPOSAL:
        icon = 'event-proposal'
    elif event.event.code in S_AMENDMENT:
        icon = 'event-amendment'
    elif event.event.code in S_DELEGATION_IN:
        icon = 'event-delegation-in'
    elif event.event.code in S_DELEGATION_OUT:
        icon = 'event-delegation-out'
    elif event.event.code in S_VOTE:
        icon = 'event-vote'
    elif event.event.code in S_BADGE:
        icon = 'event-badge'
    elif event.event.code == 't_massmessage_send':
        icon = 'event-massmessage'
    elif event.event.code in S_MESSAGE:
        icon = 'event-message'
    else:
        icon = 'event-unknown'

    return '<i class="icon-%s %s"></i>' % (icon, classes)
