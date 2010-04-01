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

import adhocracy.model as model 

from url import instance_url, entity_url
from adhocracy.i18n import relative_date, relative_time, format_date, countdown_time
from auth.csrf import url_token, field_token
from watchlist import make_watch, find_watch
 
from webhelpers.pylonslib import Flash as _Flash
import webhelpers.text as text
flash = _Flash()


@cache.memoize('delegateable_breadcrumbs')
def breadcrumbs(entity):    
    if not entity:
        return site_name()
    if isinstance(entity, model.Text):
        url = breadcrumbs(entity.page) 
        if entity.variant != model.Text.HEAD:
            url += " &raquo; <a href='%s'>%s</a>" % (entity_url(entity), 
                                                     cgi.escape(entity.variant))
        return url 
    if isinstance(entity, model.Page):
        url = breadcrumbs(entity.instance) 
        url += " &raquo; <a href='%s'>%s</a>" % (entity_url(entity), 
                                                 cgi.escape(entity.title))
        return url
    if isinstance(entity, model.User):
        return breadcrumbs(c.instance) + " &raquo; <a href='%s'>%s</a>" % (entity_url(entity),
                                                                           cgi.escape(entity.name))
    link = "<a href='%s'>%s</a>" % (entity_url(entity), 
                                    cgi.escape(text.truncate(entity.label, length=40, whole_word=True)))
    if hasattr(entity, 'parents') and len(entity.parents):
        link = breadcrumbs(entity.parents[0]) + " &raquo; " + link
    elif hasattr(entity, 'instance'):
        link = breadcrumbs(entity.instance) + " &raquo; " + link
    return link


def immutable_proposal_message():
    return _("This proposal is currently being voted on and cannot be modified.")


def user_link(user, size=16, scope=None):
    @cache.memoize('user_generic_link')
    def _generic_link(user, size, scope):
        url = "<a href='%s' class='user_link'><img class='user_icon' src='%s' alt="" /> %s</a>" % (
            entity_url(user), gravatar_url(user, size=size),
            cgi.escape(user.name))
        if scope:
            votes = user.number_of_votes_in_scope(scope)
            if votes > 0:
                url += "<sup>%s</sup>" % votes
        return url
    
    @cache.memoize('user_specific_link')
    def _specific_link(user, size, scope, other):
        url = _generic_link(user, size, scope)
        if other and scope:
            dnode = democracy.DelegationNode(other, scope)
            for delegation in dnode.outbound():
                if delegation.agent == user:
                    icon = "<img class='user_icon' src='/img/icons/delegate_16.png' />"
                    url += "<a href='%s'>%s</a>" % (entity_url(delegation), icon)
        return url
    
    return _specific_link(user, size, scope, c.user)

    
@cache.memoize('proposal_icon')
def proposal_icon(proposal, size=16):
    if proposal.adopted:
        return instance_url(None, path='') + "/img/icons/proposal_adopted_" + str(size) + ".png"
    if proposal.is_adopt_polling():
        return instance_url(None, path='') + "/img/icons/vote_" + str(size) + ".png"
    else:
        return instance_url(None, path='') + "/img/icons/proposal_" + str(size) + ".png"


@cache.memoize('delegateable_link')
def delegateable_link(delegateable, icon=True, icon_size=16, link=True):
    text = ""
    if icon:
        if isinstance(delegateable, model.Proposal):
            text = "<img class='dgb_icon' src='%s' /> " % proposal_icon(delegateable, size=icon_size)
        elif isinstance(delegateable, model.Issue):
            text = "<img class='dgb_icon' src='%s/img/icons/issue_%s.png' /> " % (
                        instance_url(None, path=''), icon_size)
    text += cgi.escape(delegateable.label)
    if link and not delegateable.delete_time:
        text = "<a href='%s' class='dgb_link'>%s</a>" % (entity_url(delegateable), text)
    return text


def tag_link(tag, count=None, size=None, base_size=12, plain=False):
    text = "<span class='tag_link %s'><a" % ("plain" if plain else "")
    if size is not None:
        size = int(math.sqrt(size) * base_size)
        text += " style='font-size: %dpx !important;'" % size
    text += " href='%s' rel='tag'>%s</a>" % (entity_url(tag), cgi.escape(tag.name))
    if count is not None and count > 1:
        text += "&thinsp;&times;" + str(count)
    text += "</span>"
    return text


def page_link(page, create=False):
    text = "<a class='page_link %s' href='%s'>%s</a>"
    if create:
        url = urllib.quote(page.encode('utf-8'))
        url = "/page/new?title=%s" % url
        return text % ('new', url, cgi.escape(page))
    else:
        return text % ('exists', entity_url(page), 
                       cgi.escape(page.title))
        
    

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


def proposal_position(topic):
    if not topic or not isinstance(topic, model.Proposal) or not c.user:
        return 0
    if not c.proposal_pos:
        c.proposal_pos = {}
    if not topic.id in c.proposal_pos:
        c.proposal_pos[topic.id] = c.user.any_position_on_proposal(topic)
    return c.proposal_pos[topic.id]


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


def add_meta(key, value):
    if not c.html_meta:
        c.html_meta = dict()
    c.html_meta[key] = value


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
