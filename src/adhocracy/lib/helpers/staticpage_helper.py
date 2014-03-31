from itertools import izip
import logging
import babel.core

from adhocracy import config
from adhocracy.lib import cache, staticpage
from adhocracy.lib.helpers import url as _url
from adhocracy.lib.helpers.adhocracy_service import RESTAPI

log = logging.getLogger(__name__)


@cache.memoize('staticpage_url')
def url(staticpage, **kwargs):
    pid = staticpage.key
    return _url.build(None, 'static', pid, **kwargs)


def get_lang_info(lang):
    locale = babel.core.Locale(lang)
    return {'id': lang, 'name': locale.language_name}


def can_edit():
    return staticpage.can_edit()


def get_body(key, default=''):
    res = staticpage.get_static_page(key)
    if res is None:
        return default
    return res.body


def render_footer_column(instance, column):
    if not config.get_bool('adhocracy.customize_footer'):
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


def breadcrumbs(staticpage):
    return _url.root() + _url.link(staticpage.title, url(staticpage))


def use_external_navigation():
    return config.get_bool('adhocracy.use_external_navigation', False)


def render_external_navigation(current_key):
    api = RESTAPI()
    base = config.get('adhocracy.kotti_navigation_base', None)
    result = api.staticpages_get(base=base)
    nav = result.json()
    if nav is None or not nav.get('children'):
        log.error('External navigation not found for configured languages')
        return ''

    def render_navigation_item(item, path='', toplevel=False):
        from adhocracy.lib.templating import render_def

        if path != '':
            path = '%s/%s' % (path, item['name'])
        else:
            path = item['name']

        url = '/static/%s.html' % path

        contains_current = (path == current_key)
        if item['children']:
            children, contained_list = izip(
                *map(lambda child: render_navigation_item(child, path),
                     item['children']))
            contains_current = contains_current or any(contained_list)
        else:
            children = []

        html = render_def('static/tiles.html', 'navigation_item',
                          href=url,
                          title=item['title'],
                          current=toplevel and contains_current,
                          children=children)

        return (html, contains_current)

    html_list, _ = izip(
        *map(lambda child: render_navigation_item(child, toplevel=True),
             nav['children']))
    return '\n'.join(html_list)
