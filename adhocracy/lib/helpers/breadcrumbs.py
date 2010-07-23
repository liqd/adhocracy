from pylons import tmpl_context as c
from pylons.i18n import _

import adhocracy.model as model
from adhocracy.lib import cache
import urllib, hashlib, cgi

from webhelpers.text import truncate

import site_helper as site

    
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
