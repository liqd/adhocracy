import babel.core

from adhocracy.lib import cache, staticpage
from adhocracy.lib.helpers import url as _url


@cache.memoize('staticpage_url')
def url(staticpage, **kwargs):
    pid = staticpage.key + '_' + staticpage.lang
    return _url.build(None, 'static', pid, **kwargs)


def get_lang_info(lang):
    locale = babel.core.Locale(lang)
    return {'id': lang, 'name': locale.display_name}


def can_edit():
    return staticpage.can_edit()


def get_body(key, default=''):
    res = staticpage.get_static_page(key)
    if res is None:
        return default
    return res.body
