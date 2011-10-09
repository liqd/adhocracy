import cgi

from pylons.i18n import _

from adhocracy.lib import cache
from adhocracy.lib.text import label2url
from adhocracy.lib.helpers import url as _url
from adhocracy.lib.helpers.site_helper import base_url


@cache.memoize('proposal_icon', 3600)
def icon_url(proposal, size=16):
    if proposal.adopted:
        return (base_url(None, path='') + u"/img/icons/proposal_adopted_" +
                str(size) + u".png")
    if proposal.is_adopt_polling():
        return (base_url(None, path='') + u"/img/icons/vote_" + str(size) +
                u".png")
    else:
        return (base_url(None, path='') + u"/img/icons/proposal_" +
                str(size) + u".png")


@cache.memoize('proposal_link', 3600)
def link(proposal, icon=False, icon_size=16, link=True, **kwargs):
    text = u""
    if icon:
        text += (u"<img class='dgb_icon' src='%s' /> " %
                 icon_url(proposal, size=icon_size))
    text += cgi.escape(proposal.title)
    if link and not proposal.is_deleted():
        text = (u"<a href='%s' class='dgb_link'>%s</a>" %
                (url(proposal, **kwargs), text))
    return text


@cache.memoize('proposal_url', 3600)
def url(proposal, **kwargs):
    ext = str(proposal.id) + '-' + label2url(proposal.title)
    return _url.build(proposal.instance, 'proposal', ext, **kwargs)


@cache.memoize('proposal_bc')
def bc_entity(proposal):
    return _url.BREAD_SEP + _url.link(proposal.title, url(proposal))


def breadcrumbs(proposal):
    bc = _url.root()
    bc += _url.link(_("Proposals"), u'/proposal')
    if proposal is not None:
        bc += bc_entity(proposal)
    return bc
