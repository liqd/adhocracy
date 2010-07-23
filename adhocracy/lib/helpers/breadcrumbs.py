from pylons import tmpl_context as c
from pylons.i18n import _

import adhocracy.model as model
from adhocracy.lib import cache
import urllib, hashlib, cgi

from webhelpers.text import truncate

import site_helper as site

SEP = u" &raquo; "

@cache.memoize('breadcrumbs')
def breadcrumbs(entity):   
    raise ValueError()
    

def root():
    return site.name()
    return _instance(proposal.instance) + SEP

def link(title, href):
    title = cgi.escape(truncate(title, length=40, whole_word=True))
    return u"<a href='%s'>%s</a>" % (href, title)
    
    
    
def _instance(instance):
    if not instance: 
        import helpers as h 
        return h.site.name()
    return _link_entity(instance.label, instance)
    
def _selection(selection):
    bc = _proposal(selection.proposal) + SEP
    bc += _link(_("Implementation"), 
                entity_url(selection.proposal, member='implementation')) + SEP
    bc += _link_entity(selection.page.title, selection)
    return bc
    
def _text(text):
    bc = _page(text.page)
    if text.variant != model.Text.HEAD:
        bc += SEP + _link_entity(text.variant, text)
    return bc
    
def _page(page):
    bc = ""
    if page.parent: 
        bc += _page(page.parent) + SEP
    else: 
        bc += _instance(page.instance) + SEP
        bc += _link(_("Documents"), u'/page') + SEP
    bc += _link_entity(page.title, page)
    return bc
    
def _proposal(proposal):
    bc = _instance(proposal.instance) + SEP
    bc += _link(_("Proposals"), u'/proposal') + SEP
    bc += _link_entity(proposal.label, proposal)
    return bc
    
def _user(user):
    bc = _instance(c.instance) + SEP
    bc += _link(_("Users"), u'/user') + SEP
    bc += _link_entity(user.name, user)
    return bc
