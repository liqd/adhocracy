from pylons import tmpl_context as c
from pylons.i18n import _

import adhocracy.model as model
import cache
import urllib, hashlib, cgi
from url import instance_url, entity_url
import webhelpers.text as text

@cache.memoize('delegateable_breadcrumbs')
def breadcrumbs(entity):    
    if not entity:
        import helpers as h 
        return h.site_name()
    if isinstance(entity, model.Text):
        return _text(entity)
    if isinstance(entity, model.Page):
        return _variant(entity)
    if isinstance(entity, model.User):
        return _user(entity)
    if isinstance(entity, model.Proposal):
        return _proposal(entity)
    return _link_entity(entity.label, entity)


def _link_entity(title, entity):
    return _link(title, entity_url(entity))

def _link(title, href):
    return "<a href='%s'>%s</a>" % (href, cgi.escape(text.truncate(title, length=40, whole_word=True)))
    
def _instance(instance):
    return _link_entity(instance.label, instance)
    
def _text(text):
    bc = _page(text.page)
    if text.variant != model.Text.HEAD:
        bc += " &raquo; " + _link_entity(text.variant, text)
    return bc
    
def _page(page):
    bc = _instance(page.instance) + " &raquo; "
    bc += _link(_("Pages"), '/page') + " &raquo; "
    bc += _link_entity(page.title, page)
    return bc
    
def _proposal(proposal):
    bc = _instance(proposal.instance) + " &raquo; "
    bc += _link(_("Proposals"), '/proposal') + " &raquo; "
    bc += _link_entity(proposal.label, proposal)
    return bc
    
def _user(user):
    bc = _instance(c.instance) + " &raquo; "
    bc += _link(_("Users"), '/user') + " &raquo; "
    bc += _link_entity(user.name, user)
    return bc
