import urllib

from paste.deploy.converters import asbool
from pylons import config

from adhocracy.lib import cache
from adhocracy.lib.helpers import url as _url


@cache.memoize('text_url')
def url(text, **kwargs):
    import page_helper as page
    if text is None:
        return ''
    in_context = (text == text.page.variant_head(text.variant))
    url = page.url(text.page, in_context=in_context)
    if text.page.has_variants and text.variant != text.HEAD:
        url += u'/' + urllib.quote(text.variant.encode('utf-8'))
    if text != text.page.variant_head(text.variant):
        url += u';' + str(text.id)
    return _url.append_member_and_format(url, **kwargs)


@cache.memoize('text_bc')
def entity_bc(text):
    return _url.BREAD_SEP + _url.link(text.variant, url(text))


def breadcrumbs(text):
    import page_helper as page
    bc = page.breadcrumbs(text.page)
    if text is not None and text.variant != text.HEAD:
        bc += entity_bc(text)
    return bc


def getconf_allow_user_html(_testing_override=None):
    if _testing_override is not None:
        return _testing_override
    return asbool(config.get('adhocracy.allow_user_html', 'true'))
