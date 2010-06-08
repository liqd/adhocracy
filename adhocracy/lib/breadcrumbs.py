from pylons import tmpl_context as c
from pylons.i18n import _

import adhocracy.model as model
import cache
import urllib, hashlib, cgi
from url import instance_url, entity_url
import webhelpers.text as text

SEP = " &raquo; "

@cache.memoize('delegateable_breadcrumbs')
def breadcrumbs(entity):    
    if not entity:
        import helpers as h 
        return h.site_name()
    if isinstance(entity, model.Text):
        return _text(entity)
    if isinstance(entity, model.Page):
        return _page(entity)
    if isinstance(entity, model.User):
        return _user(entity)
    if isinstance(entity, model.Proposal):
        return _proposal(entity)
    if isinstance(entity, model.Selection):
        return _selection(entity)
    return _link_entity(entity.label, entity)


def _link_entity(title, entity):
    return _link(title, entity_url(entity))

def _link(title, href):
    return "<a href='%s'>%s</a>" % (href, cgi.escape(text.truncate(title, length=40, whole_word=True)))
    
def _instance(instance):
    if not instance: 
        import helpers as h 
        return h.site_name()
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
        bc += _link(_("Documents"), '/page') + SEP
    bc += _link_entity(page.title, page)
    return bc
    
def _proposal(proposal):
    bc = _instance(proposal.instance) + SEP
    bc += _link(_("Proposals"), '/proposal') + SEP
    bc += _link_entity(proposal.label, proposal)
    return bc
    
def _user(user):
    bc = _instance(c.instance) + SEP
    bc += _link(_("Users"), '/user') + SEP
    bc += _link_entity(user.name, user)
    return bc
