import cgi 

import adhocracy.model as model
from adhocracy.lib import cache

import page_helper as page
import proposal_helper as proposal
import url as _url


@cache.memoize('delegateable_link')
def link(delegateable, icon=True, icon_size=16, link=True):
    if isinstance(delegateable, model.Proposal):
        return proposal.link(delegateable, icon=icon, icon_size=icon_size, link=link)
    elif isinstance(delegateable, model.Page):
        return page.link(delegateable, icon=icon, icon_size=icon_size, link=link)
    return cgi.escape(delegateable.title)