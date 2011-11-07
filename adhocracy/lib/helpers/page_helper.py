import cgi
import urllib

from pylons.i18n import _

from adhocracy import  model
from adhocracy.lib import cache
from adhocracy.lib.helpers import proposal_helper as proposal
from adhocracy.lib.helpers import url as _url


def icon_url(page, size=16):
    import text_helper as text
    return text.icon_url(page.head, page, size=size)


@cache.memoize('page_link')
def link(page, variant=model.Text.HEAD, link=True, icon=False, icon_size=16):
    import text_helper as text
    buf = cgi.escape(page.title)
    text_ = page.variant_head(variant)
    if text_ is None:
        return _("(Unknown)")
    if variant != text_.HEAD:
        buf = u"%s <code>(%s)</code>" % (buf, variant)
    if icon:
        buf = (u"<img class='dgb_icon' src='%s' /> %s" %
               (text.icon_url(text_, page, size=icon_size), buf))
    if link and not page.is_deleted():
        buf = (u"<a class='page_link exists' href='%s'>%s</a>" %
               (text.url(text_), buf))
    return buf


@cache.memoize('page_url')
def url(page, in_context=True, member=None, **kwargs):
    if in_context and page.proposal and not member:
        return proposal.url(page.proposal, **kwargs)
    label = urllib.quote(page.label.encode('utf-8'))
    return _url.build(page.instance, 'page', label, member=member, **kwargs)


def page_variant_url(page, variant):
    '''
    TODO: Hacked together to implement new page views.
    Refactor url functions.
    '''
    label = urllib.quote(page.label.encode('utf-8'))
    if variant == model.Text.HEAD:
        variant = None
    else:
        variant = urllib.quote(variant.encode('utf-8'))
    return _url.build(page.instance, 'page', label, member=variant)


@cache.memoize('page_bc', time=3600)
def entity_bc(page):
    bc = ''
    if page.parent:
        bc += entity_bc(page.parent)
    return bc + _url.BREAD_SEP + _url.link(page.title, url(page))


def breadcrumbs(page):
    bc = _url.root()
    bc += _url.link(_("Documents"), u'/page')
    if page is not None:
        bc += entity_bc(page)
    return bc
