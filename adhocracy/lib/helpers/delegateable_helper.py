import cgi

from adhocracy import model
from adhocracy.lib import cache

import page_helper as page
import proposal_helper as proposal


@cache.memoize('delegateable_link')
def link(delegateable, icon=False, icon_size=16, link=True):
    if isinstance(delegateable, model.Proposal):
        return proposal.link(delegateable, icon=icon, icon_size=icon_size,
                             link=link)
    elif isinstance(delegateable, model.Page):
        return page.link(delegateable, link=link)
    return cgi.escape(delegateable.title)


@cache.memoize('delegateable_bc')
def breadcrumbs(delegateable):
    if isinstance(delegateable, model.Proposal):
        return proposal.breadcrumbs(delegateable)
    elif isinstance(delegateable, model.Page):
        return page.breadcrumbs(delegateable)
    return cgi.escape(delegateable.title)
