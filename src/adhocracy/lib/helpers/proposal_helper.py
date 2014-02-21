import cgi

from pylons.i18n import _
from pylons import tmpl_context as c

from adhocracy.lib import cache
from adhocracy.lib.text import label2url
from adhocracy.lib.helpers import url as _url
from adhocracy.lib.helpers.category_helper import bc_entity as bc_category


@cache.memoize('proposal_link', 3600)
def link(proposal, link=True, **kwargs):
    text = cgi.escape(proposal.title)
    if link and not proposal.is_deleted():
        text = (u"<a href='%s' class='dgb_link'>%s</a>" %
                (url(proposal, **kwargs), text))
    return text


@cache.memoize('proposal_url', 3600)
def url(proposal, member=None, in_overlay=True, **kwargs):
    if proposal.is_amendment and member is None:
        base = u'page/%s/amendment' % proposal.selection.page.label
        if in_overlay:
            from adhocracy.lib.helpers import page_helper as page
            kwargs[u'format'] = u'overlay'
            query = {
                u'overlay_path': _url.build(proposal.instance, base,
                                            proposal.id, **kwargs),
                u'overlay_type': u'#overlay-url-big',
            }
            return page.url(proposal.selection.page, query=query)
        else:
            return _url.build(proposal.instance, base, proposal.id, **kwargs)
    else:
        ext = str(proposal.id) + '-' + label2url(proposal.title)
        return _url.build(proposal.instance, 'proposal', ext,
                          member=member, **kwargs)


@cache.memoize('proposal_bc')
def bc_entity(proposal):
    return _url.BREAD_SEP + _url.link(proposal.title, url(proposal))


def breadcrumbs(proposal):
    from adhocracy.lib.helpers import base_url
    bc = _url.root()
    if c.instance.show_proposals_navigation:
        bc += _url.link(_("Proposals"), base_url(u'/proposal'))
    elif c.instance.display_category_pages:
        bc += _url.link(_("Categories"), base_url(u'/category'))

        if proposal is not None and proposal.category is not None:
            bc += bc_category(proposal.category)
    else:
        # FIXME this case will produce a double BREAD_SEP
        pass
    if proposal is not None:
        bc += bc_entity(proposal)
    return bc
