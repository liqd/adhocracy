import cgi
import urllib

from pylons.i18n import _

from adhocracy import model
from adhocracy.lib import cache
from adhocracy.lib.helpers import proposal_helper as proposal
from adhocracy.lib.helpers import url as _url


@cache.memoize('page_link')
def link(page, variant=model.Text.HEAD, link=True):
    import text_helper as text
    buf = cgi.escape(page.title)
    text_ = page.variant_head(variant)
    if text_ is None:
        return _("(Unknown)")
    if variant != text_.HEAD:
        buf = u"%s <code>(%s)</code>" % (buf, variant)
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


def page_text_url(page, text, member=None):
    label = '%s;%d' % (urllib.quote(page.label.encode('utf-8')), text.id)
    return _url.build(page.instance, 'page', label, member=member)


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
