"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password

import urllib, hashlib, cgi

from pylons import tmpl_context as c, config, request
from pylons.i18n import _

from adhocracy.lib.auth.authorization import has as has_permission
from adhocracy.lib import democracy
from adhocracy.lib import cache
from adhocracy.lib import sorting

import adhocracy.model as model 

from adhocracy.i18n import relative_date, relative_time, format_date, countdown_time
from adhocracy.lib.auth.csrf import url_token, field_token
from adhocracy.lib.watchlist import make_watch, find_watch
 
from webhelpers.pylonslib import Flash as _Flash
from webhelpers.text import truncate

flash = _Flash()

import site_helper as site
import user_helper as user
import proposal_helper as proposal
import text_helper as text
import page_helper as page
import delegateable_helper as delegateable
import tag_helper as tag
import poll_helper as poll
import comment_helper as comment
import selection_helper as selection
import delegation_helper as delegation
import instance_helper as instance
import abuse_helper as abuse

from site_helper import base_url
#from breadcrumbs import breadcrumbs


def immutable_proposal_message():
    return _("This proposal is currently being voted on and cannot be modified.")


def comments_sorted(comments, root=None, variant=None):
    from adhocracy.lib.tiles.comment_tiles import CommentTile
    comments = [c for c in comments if c.variant==variant and c.reply==root]
    _comments = []
    for comment in sorting.comment_order(comments):
        tile = CommentTile(comment)
        _comments.append((comment, tile))
    return _comments


def contains_delegations(user, delegateable, recurse=True):
    for delegation in user.agencies:
        if not delegation.revoke_time and (delegation.scope == delegateable or \
            (delegation.scope.is_sub(delegateable) and recurse)):
            return True
    for delegation in user.delegated:
        if not delegation.revoke_time and (delegation.scope == delegateable or \
            (delegation.scope.is_sub(delegateable) and recurse)):
            return True
    return False


def poll_position_css(poll):
    @cache.memoize('poll_position_css')
    def _cached(user, poll):
        pos = user.position_on_poll(poll)
        if pos == 1:
            return "upvoted"
        elif pos == -1:
            return "downvoted"
        else:
            return ""
    if c.user:
        return _cached(c.user, poll)
    return u""
        








def propose_comment_title(parent=None, topic=None, variant=None):
    if parent and parent.latest.title:
        title = parent.latest.title
        if not title.startswith(_("Re: ")):
            title = _("Re: ") + title
        return title
    elif variant and variant != model.Text.HEAD:
        return _("Re: ") + variant[:250]
    elif topic:
        return _("Re: ") + topic.title[:250]
    return ""
    

def add_meta(key, value):
    if not c.html_meta:
        c.html_meta = dict()
    c.html_meta[key] = value

def help_link(text, page, anchor=None):
    url = base_url(None, path="/static/%s.%s")
    if anchor is not None:
        url += "#" + anchor
    full_url = url % (page, 'html')
    simple_url = url % (page, 'simple')
    return u"<a target='_new' href='%s' onClick='return showHelp(\"%s\")'>%s</a>" % (full_url, simple_url, text)



def add_rss(title, link):
    if not c.html_link:
        c.html_link = []
    c.html_link.append({'title': title, 
                        'href': link, 
                        'rel': 'alternate',
                        'type': 'application/rss+xml'})


def entity_url(entity, **kwargs):
    if isinstance(entity, model.User):
        return user.url(entity, **kwargs)
    elif isinstance(entity, model.Proposal):
        return proposal.url(entity, **kwargs)
    elif isinstance(entity, model.Page):
        return page.url(entity, **kwargs)
    elif isinstance(entity, model.Text):
        return text.url(entity, **kwargs)
    elif isinstance(entity, model.Delegateable):
        return delegateable_url(entity, **kwargs)
    elif isinstance(entity, model.Poll):
        return poll.url(entity, **kwargs)
    elif isinstance(entity, model.Selection):
        return selection.url(entity, **kwargs)
    elif isinstance(entity, model.Comment):
        return comment.url(entity, **kwargs)
    elif isinstance(entity, model.Instance):
        return instance.url(entity, **kwargs)
    elif isinstance(entity, model.Delegation):
        return delegation.url(entity, **kwargs)
    elif isinstance(entity, model.Tag):
        return tag.url(entity, **kwargs)
    raise ValueError("No URL maker for: %s" % repr(entity))