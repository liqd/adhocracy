from itertools import izip
import logging
import babel.core
from requests import ConnectionError
from simplejson.scanner import JSONDecodeError

from pylons import tmpl_context as c

from adhocracy import config
from adhocracy.lib import cache, staticpage
from adhocracy.lib.helpers import url as _url
from adhocracy.lib.helpers.adhocracy_service import RESTAPI
from adhocracy.lib.helpers.adhocracy_service import \
    instance_staticpages_api_address

log = logging.getLogger(__name__)


@cache.memoize('staticpage_url')
def url(staticpage, **kwargs):
    instance = c.instance if instance_staticpages_api_address() else None
    pid = staticpage.key
    return _url.build(instance, 'static', pid, **kwargs)


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
    if not use_external_navigation():
        return None
    api = RESTAPI()
    base = config.get('adhocracy.external_navigation_base')
    try:
        result = api.staticpages_get(base=base)
    except ConnectionError as e:
        log.error('Error while connecting to static pages backend: %s' % e)
        return None
    if not result.ok:
        log.error('Error while fetching static pages: %s %s'
                  % (result.status_code, result.reason))
        return None
    try:
        nav = result.json()
    except JSONDecodeError as e:
        log.error('Error while decoding static pages: %s' % e)
        return None
    instance = c.instance if instance_staticpages_api_address() else None
    if nav is None or not nav.get('children'):
        log.error('External navigation not found for configured languages')
        return None

    def render_navigation_item(item, path='', toplevel=False):
        from adhocracy.lib.templating import render_def

        if path != '':
            path = '%s/%s' % (path, item['name'])
        else:
            path = item['name']

        url = _url.build(instance, 'static', path, format='html')

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
