import logging
import os.path
import re

import adhocracy.model
from adhocracy import i18n
from adhocracy.lib.helpers.adhocracy_service import RESTAPI
from adhocracy.lib import util
from adhocracy.lib.auth.authorization import has
from adhocracy.lib.outgoing_link import rewrite_urls


from lxml.html import parse, tostring
from pylons import config

log = logging.getLogger(__name__)


class StaticPageBase(object):

    def __init__(self, key, lang, body, title):
        self.key = key
        self.lang = lang
        self.title = title
        self.body = body

    @staticmethod
    def get(key, lang):
        fn = os.path.basename(key) + '.' + lang + '.html'
        filename = util.get_path('page', fn)
        if filename is None:
            return None
        try:
            root = parse(filename)
        except IOError:
            return None
        try:
            body = root.find('.//body')
            title = root.find('.//title').text
        except AttributeError:
            log.debug(u'Failed to parse static document ' + filename)
            return None
        body.tag = 'span'
        return FileStaticPage(key, lang, tostring(body), title)

    def commit(self):
        """ Persist changes to this object. """
        raise NotImplementedError()

    @staticmethod
    def all():
        raise NotImplementedError()

    def save(self):
        raise NotImplementedError()

    @staticmethod
    def create(key, lang, title, body):
        raise NotImplementedError()

    @staticmethod
    def is_editable():
        return False


class FileStaticPage(StaticPageBase):

    @staticmethod
    def get(key, languages):

        for lang in languages:
            fn = os.path.basename(key) + '.' + lang + '.html'
            filename = util.get_path('page', fn)
            if filename is not None:
                try:
                    root = parse(filename)
                except IOError:
                    return None
                try:
                    body = root.find('.//body')
                    title = root.find('.//title').text
                except AttributeError:
                    log.debug(
                        u'Failed to parse static document ' + filename)
                    return None
                body.tag = 'span'
                return FileStaticPage(key, lang, tostring(body), title)
        return None


class KottiStaticPage(StaticPageBase):

    @staticmethod
    def get(key, languages):
        api = RESTAPI()
        result = api.staticpage_get(key)
        page = result.json()
        if page is None:
            return None
        return KottiStaticPage(key, page['lang'], page['body'], page['title'])

_BACKENDS = {
    'filesystem': FileStaticPage,
    'database': adhocracy.model.StaticPage,
    'kotti': KottiStaticPage,
}

STATICPAGE_KEY = re.compile(r'^[a-z0-9_-]+$')


def get_backend():
    backend_id = config.get('adhocracy.staticpage_backend', 'filesystem')
    return _BACKENDS[backend_id]


def can_edit():
    if not get_backend().is_editable():
        return False
    return has('global.staticpage')


def render_body(body):
    return rewrite_urls(body)


def get_static_page(key, language=None):
    backend = get_backend()
    if language is None:
        page = backend.get(key, i18n.all_languages(include_preferences=True))
    else:
        page = backend.get(key, [language])
    return page


def add_static_content(data, config_key, title_key=u'title',
                       body_key=u'body'):

    static_path = config.get(config_key)
    if static_path is not None:
        page = get_static_page(static_path)
        if page is None:
            data[title_key] = data[body_key] = None
        else:
            data[title_key] = page.title
            data[body_key] = render_body(page.body)
    else:
        data[title_key] = data[body_key] = None
