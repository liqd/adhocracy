import logging
import babel.core

from adhocracy import config
from adhocracy.lib import cache, staticpage
from adhocracy.lib.helpers import url as _url
from adhocracy.lib.helpers.adhocracy_service import RESTAPI

log = logging.getLogger(__name__)


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


def use_kotti_navigation():
    return config.get_bool('adhocracy.use_kotti_navigation', False)


def render_kotti_navigation():
    api = RESTAPI()
    base = config.get('adhocracy.kotti_navigation_base', None)
    result = api.staticpages_get(base=base)
    nav = result.json()
    if nav is None or not nav.get('children'):
        log.error('Kotti based navigation not found for configured languages')
        return ''

    def render_navigation_item(item, path=''):

        if path != '':
            path = '%s/%s' % (path, item['name'])
        else:
            path = item['name']

        self_html = u'<a href="%s">%s</a>' % (path, item['title'])

        if item['children']:
            children_html = u'\n<ul class="children">\n%s\n</ul>\n' % (
                '\n'.join(
                    map(lambda child: render_navigation_item(child, path),
                        item['children'])))
        else:
            children_html = ''

        return '<li>%s%s</li>' % (self_html, children_html)

    return '\n'.join(map(render_navigation_item, nav['children']))
