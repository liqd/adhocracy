from pylons.i18n import _

from adhocracy.lib import cache

import proposal_helper as proposal
import url as _url


@cache.memoize('selection_url')
def url(selection, **kwargs):
    url = proposal.url(selection.proposal, member='implementation')
    url += "/" + str(selection.id)
    return _url.append_member_and_format(url, **kwargs)


@cache.memoize('selection_bc')
def breadcrumbs(selection):
    bc = _url.root()
    if selection is not None:
        bc += _url.link(_("Implementation"), 
                        proposal.url(selection.proposal, member=u'/implementation'))
        bc += _url.BREAD_SEP + _url.link(selection.page.title, url(selection))
    else:
        bc += _("Implementation")
    return bc
