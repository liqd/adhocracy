import cgi

from pylons.i18n import _

from adhocracy import model
from adhocracy.lib import cache, logo
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


def logo_url(page, y, x=None):
    from adhocracy.lib.helpers import base_url
    size = "%s" % y if x is None else "%sx%s" % (x, y)
    filename = u"%s_%s.png" % (page.id, size)
    (path, mtime) = logo.path_and_mtime(page)
    return base_url(u'/page/%s' % filename, query_params={'t': str(mtime)})


@cache.memoize('page_url')
def url(page, in_context=True, member=None, **kwargs):
    if in_context and page.proposal and not member:
        return proposal.url(page.proposal, **kwargs)
    if (in_context and member is None and page.is_sectionpage() and
            page.sectionpage_root() != page):
        if u'anchor' not in kwargs:
            kwargs[u'anchor'] = u'subpage-%i' % page.id
        return url(page.sectionpage_root(), in_context=False, **kwargs)
    label = _url.quote(page.label)
    return _url.build(page.instance, 'page', label, member=member, **kwargs)


def page_variant_url(page, variant):
    '''
    TODO: Hacked together to implement new page views.
    Refactor url functions.
    '''
    label = _url.quote(page.label)
    if variant == model.Text.HEAD:
        variant = None
    else:
        variant = _url.quote(variant)
    return _url.build(page.instance, 'page', label, member=variant)


def page_text_url(page, text, member=None):
    label = '%s;%d' % (_url.quote(page.label), text.id)
    return _url.build(page.instance, 'page', label, member=member)


@cache.memoize('page_bc', time=3600)
def entity_bc(page):
    bc = ''
    if page.parent:
        bc += entity_bc(page.parent)
    return bc + _url.BREAD_SEP + _url.link(page.title, url(page))


def breadcrumbs(page):
    from adhocracy.lib.helpers import base_url
    bc = _url.root()
    bc += _url.link(_("Norms"), base_url(u'/page'))
    if page is not None:
        bc += entity_bc(page)
    return bc
