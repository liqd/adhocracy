"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password

import urllib, hashlib, cgi

from pylons import tmpl_context as c
from pylons import request
from pylons.i18n import add_fallback, get_lang, set_lang, gettext, _

import authorization 
import karma 
import democracy
import cache

import adhocracy.model as model 

from text.i18n import relative_date, relative_time, format_timedelta
from xsrf import url_token, field_token
from karma import user_score as user_karma
 
from webhelpers.pylonslib import Flash as _Flash
import webhelpers.text as text
flash = _Flash()


def breadcrumbs(delegateable, id=None):
    import adhocracy.model as model
    
    if not delegateable:
        return _("Adhocracy")
    
    if not id:
        id = delegateable.id
    
    if len(delegateable.parents):
        link = "<a href='/d/%s'>%s</a>" % (id, text.truncate(delegateable.label, length=30, whole_word=True))
        link = breadcrumbs(delegateable.parents[0]) + " &raquo; " + link
    else:
        link = "<a href='/category/%s'>%s</a>" % (delegateable.instance.root.id, 
                                                  text.truncate(delegateable.instance.label, length=30, whole_word=True))
    return link

def has_permission(permission):
    p = authorization.has_permission(permission)
    return p.is_met(request.environ)

def immutable_motion_message():
    return _("This motion is currently being voted on and cannot be modified.")

def user_link(user, size=16, link=None):
    if not link:
        link = "/user/%s" % user.user_name
    return "<a href='%s' class='user_link'><img class='user_icon' src='%s' alt="" /> %s</a><sup>%s</sup>" % (
        instance_url(c.instance, path=link), 
        gravatar_url(user, size=size),
        cgi.escape(user.name),
        karma.user_score(user))
    
@cache.memoize('motion_icon', 3600*2)
def motion_icon(motion, size=16):
    state = democracy.State(motion)
    if state.adopted:
        return instance_url(None, path='') + "/img/icons/motion_adopted_" + str(size) + ".png"
    else:
        return instance_url(None, path='') + "/img/icons/motion_" + str(size) + ".png"

def delegateable_link(delegateable, icon=True, link=True):
    text = ""
    if icon:
        if isinstance(delegateable, model.Motion):
            text = "<img class='user_icon' src='%s' /> " % motion_icon(delegateable)
        elif isinstance(delegateable, model.Issue):
            text = "<img class='user_icon' src='%s/img/icons/issue_16.png' /> " % instance_url(None, path='')
        elif isinstance(delegateable, model.Category):
            text = "<img class='user_icon' src='%s/img/icons/stack_16.png' /> " % instance_url(None, path='')
    text += cgi.escape(delegateable.label)
    if isinstance(delegateable, model.Motion) and icon:
        state = democracy.State(delegateable)
        if state.polling:
            text += " <img class='user_icon' src='/img/icons/vote_16.png' />"
    
    if link and not delegateable.delete_time:
        if isinstance(delegateable, model.Motion):
            text = "<a href='%s' class='dgb_link'>%s</a>" % (
                        instance_url(delegateable.instance, path='/motion/%s' % delegateable.id), text)
        elif isinstance(delegateable, model.Issue):
            text = "<a href='%s' class='dgb_link'>%s</a>" % (
                        instance_url(delegateable.instance, path='/issue/%s' % delegateable.id), text)
        elif isinstance(delegateable, model.Category):
            text = "<a href='%s' class='dgb_link'>%s</a>" % (
                        instance_url(delegateable.instance, path='/category/%s' % delegateable.id), text)
    return text

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
        
    

#default_gravatar = "http://adhocracy.cc/img/icons/user_%s.png"
def gravatar_url(user, size=32):
    # construct the url
    gravatar_url = "http://www.gravatar.com/avatar.php?"
    gravatar_url += urllib.urlencode({'gravatar_id':hashlib.md5(user.email).hexdigest(), 
        'default':'identicon', 
        'size': str(size)})
    return gravatar_url
    
def user_or_you(user):
    if user == c.user:
        return _("You")
    return "<a href='/user/%s'>%s</a>" % (user.user_name, cgi.escape(user.name))

def instance_url(instance, path="/"):
    subdomain = ""
    if instance: # don't ask
        subdomain = instance.key + "."
    return str("http://%s%s%s" % (subdomain,
                               request.environ['adhocracy.active.domain'],
                               path))
    
def add_meta(key, value):
    if not c.html_meta:
        c.html_meta = dict()
    c.html_meta[key] = value
    
def add_rss(title, link):
    if not c.html_link:
        c.html_link = []
    c.html_link.append({'title': title, 
                        'href': link, 
                        'rel': 'alternate',
                        'type': 'application/rss+xml'})
    
def rss_link(link):
    return "<a class='rss_link' href='%s'><img src='/img/rss.png' /></a>" % link
                                