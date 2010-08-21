from pylons.i18n import _

from adhocracy.lib import cache

import proposal_helper as proposal
import url as _url


@cache.memoize('selection_url')
def url(selection, member=None, format='html', **kwargs):
    if member is None and format == 'html':
        anchor = "selection_%s" % selection.id
        return proposal.url(selection.proposal, anchor=anchor)
    url = proposal.url(selection.proposal, member='implementation')
    url += "/" + str(selection.id)
    return _url.append_member_and_format(url, member=member, format=format, **kwargs)


@cache.memoize('selection_bc')
def bc_entity(selection):
    bc = _url.link(_("Implementation"), 
                    proposal.url(selection.proposal, member=u'/implementation'))
    bc += _url.BREAD_SEP + _url.link(selection.page.title, url(selection))
    return bc


def breadcrumbs(selection):
    bc = _url.root()
    if selection is not None:
        bc = bc_entity(selection)
    else:
        bc += _("Implementation")
    return bc
