import babel.core

from adhocracy import config
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


def render_footer_column(instance, column):
    if not config.get('adhocracy.customize_footer'):
        return None
    path = u'footer_' + unicode(column)
    if instance and\
       instance.key in config.get('adhocracy.instance_footers'):
        path = u'%s_%s' % (path, instance.key)
    page = staticpage.get_static_page(path)
    if page is None:
        return None
    else:
        return page.body
