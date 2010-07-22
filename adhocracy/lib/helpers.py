"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password

import urllib, hashlib, cgi, math

from pylons import tmpl_context as c, config, request
from pylons.i18n import add_fallback, get_lang, set_lang, gettext, _

from auth import authorization
from auth.authorization import has_permission_bool as has_permission
import democracy
import cache
import sorting

from text import html_diff

import adhocracy.model as model 

from url import instance_url, entity_url
from adhocracy.i18n import relative_date, relative_time, format_date, countdown_time
from auth.csrf import url_token, field_token
from watchlist import make_watch, find_watch
 
from webhelpers.pylonslib import Flash as _Flash
import webhelpers.text as text
flash = _Flash()

from breadcrumbs import breadcrumbs


def immutable_proposal_message():
    return _("This proposal is currently being voted on and cannot be modified.")


def user_link(user, size=16, scope=None):
    @cache.memoize('user_generic_link')
    def _generic_link(user, size, scope):
        url = u"<a href='%s' class='user_link'><img width='16' height='16' class='user_icon' src='%s' alt="" /> %s</a>" % (
            entity_url(user), gravatar_url(user, size=size),
            cgi.escape(user.name))
        if scope and ((not c.instance) or c.instance.allow_delegate):
            votes = user.number_of_votes_in_scope(scope)
            if votes > 0:
                url += u"<sup>%s</sup>" % votes
        return url
    
    @cache.memoize('user_specific_link')
    def _specific_link(user, size, scope, other):
        url = _generic_link(user, size, scope)
        if other and scope:
            dnode = democracy.DelegationNode(other, scope)
            for delegation in dnode.outbound():
                if delegation.agent == user:
                    icon = u"<img class='user_icon' width='16' height='16' src='/img/icons/delegate_16.png' />"
                    url += u"<a href='%s'>%s</a>" % (entity_url(delegation), icon)
        return url
    
    return _specific_link(user, size, scope, c.user)

    
@cache.memoize('proposal_icon')
def proposal_icon(proposal, size=16):
    if proposal.adopted:
        return instance_url(None, path='') + u"/img/icons/proposal_adopted_" + str(size) + u".png"
    if proposal.is_adopt_polling():
        return instance_url(None, path='') + u"/img/icons/vote_" + str(size) + u".png"
    else:
        return instance_url(None, path='') + u"/img/icons/proposal_" + str(size) + u".png"


@cache.memoize('delegateable_link')
def delegateable_link(delegateable, icon=True, icon_size=16, link=True):
    if isinstance(delegateable, model.Proposal):
        return proposal_link(delegateable, icon=icon, icon_size=icon_size, link=link)
    elif isinstance(delegateable, model.Page):
        return page_link(delegateable, icon=icon, icon_size=icon_size, link=link)
    return cgi.escape(delegateable.label)


def tag_link(tag, count=None, size=None, base_size=12, plain=False):
    text = u"<span class='tag_link %s'><a" % ("plain" if plain else "")
    if size is not None:
        size = int(math.sqrt(size) * base_size)
        text += u" style='font-size: %dpx !important;'" % size
    text += u" href='%s' rel='tag'>%s</a>" % (entity_url(tag), cgi.escape(tag.name))
    if count is not None and count > 1:
        text += u"&thinsp;&times;" + str(count)
    text += u"</span>"
    return text


def page_icon(page, size=16):
    return text_icon(page.head, page, size=size)
    

@cache.memoize('text_icon')        
def text_icon(text, page=None, size=16):
    if page is None:
        page = page
    path = u"/img/icons/page%s_%s.png"
    if page.function == page.NORM: 
        if text.variant != text.HEAD:
            return path % ("_variant", size)
        return path % ("_norm", size)
    elif page.function == page.DESCRIPTION:
        return proposal_icon(page.proposal, size=size)
    else:
        return path % ("", size)


def page_link(page, variant=model.Text.HEAD, create=False, link=True, icon=True, icon_size=16):
    if create:
        page = page.encode('utf-8').replace("&lt;", "<")
        page = page.replace("&gt;", ">")
        page = page.replace("&amp;", "&")
        url = urllib.quote(page)
        url = u"/page/new?title=%s" % url
        url = instance_url(c.instance, path=url)
        return u"<a class='page_link new' href='%s'>%s</a>" % (url.encode('utf-8'), 
                                                               page.encode('utf-8'))
    
    if page.is_deleted():
        link = False
    
    if not link:
        return cgi.escape(page.title)
    
    text = u""
    _text = page.variant_head(variant)
    if icon: 
        text += u"<img class='dgb_icon' src='%s' /> " % text_icon(_text, page, size=icon_size)
    text += u"<a class='page_link exists' href='%s'>%s</a>"
    title = page.title
    if variant != model.Text.HEAD:
        title = u"%s <code>(%s)</code>" % (title, variant)
    return text % (entity_url(_text), cgi.escape(title))


def proposal_link(proposal, icon=True, icon_size=16, link=True):
    text = u""
    if icon:
        text += u"<img class='dgb_icon' src='%s' /> " % proposal_icon(proposal, size=icon_size)
    text += cgi.escape(proposal.title)
    if link and not proposal.is_deleted():
        text = u"<a href='%s' class='dgb_link'>%s</a>" % (entity_url(proposal), text)
    return text


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

    
def context_instances(count=5):
    ins = c.user.instances if c.user else model.Instance.all(limit=count)
    if c.instance and c.instance in ins:
        ins.remove(c.instance)
    return sorting.instance_label(ins)


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
        

def gravatar_url(user, size=32):
    id = user.email if user.email else user.user_name
    gravatar_url = "http://www.gravatar.com/avatar.php?"
    gravatar_url += urllib.urlencode({
        'gravatar_id': hashlib.md5(id).hexdigest(), 
        'default': 'identicon', 
        'size': str(size)})
    return gravatar_url


def site_name():
    return config.get('adhocracy.site.name', _("Adhocracy"))


def canonical_url(url):
    c.canonical_url = url


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
    url = instance_url(None, path="/static/%s.%s")
    if anchor is not None:
        url += "#" + anchor
    full_url = url % (page, 'html')
    simple_url = url % (page, 'simple')
    return u"<a target='_new' href='%s' onClick='return showHelp(\"%s\")'>%s</a>" % (full_url, simple_url, text)

def rss_button(entity):
    return ""
    return "<a href='%s' class='button edit'><img src='/img/rss.png' /> %s</a>" % (
                entity_url(entity, format='rss'), _("subscribe"))


def add_rss(title, link):
    if not c.html_link:
        c.html_link = []
    c.html_link.append({'title': title, 
                        'href': link, 
                        'rel': 'alternate',
                        'type': 'application/rss+xml'})
