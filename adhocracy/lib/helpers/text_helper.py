import urllib

from pylons.i18n import _

from adhocracy.lib import cache

import proposal_helper as proposal
import url as _url


@cache.memoize('text_url')
def url(text, **kwargs):
    import page_helper as page
    url = page.url(text.page, in_context=text == text.page.variant_head(text.variant))
    if text.page.has_variants and text.variant != text.HEAD:
        url += u'/' + urllib.quote(text.variant.encode('utf-8'))
    if text != text.page.variant_head(text.variant):
        url += u';' + str(text.id)
    return _url.append_member_and_format(url, **kwargs)

  
@cache.memoize('text_icon')        
def icon_url(text, page=None, size=16):
    if page is None:
        page = text.page
    path = u"/img/icons/page%s_%s.png"
    if page.function == page.NORM: 
        if text.variant != text.HEAD:
            return path % ("_variant", size)
        return path % ("_norm", size)
    elif page.function == page.DESCRIPTION:
        return proposal.icon_url(page.proposal, size=size)
    else:
        return path % ("", size)


@cache.memoize('text_bc')
def entity_bc(text):
    return _url.BREAD_SEP + _url.link(text.variant, url(text))

def breadcrumbs(text):
    import page_helper as page
    bc = page.breadcrumbs(text.page)
    if text is not None and text.variant != text.HEAD:
        bc += entity_bc(text)
    return bc
