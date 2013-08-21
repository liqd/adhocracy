import logging
import os.path
import re

import adhocracy.model
from adhocracy import i18n
from adhocracy.lib import util
from adhocracy.lib.auth.authorization import has
from adhocracy.lib.outgoing_link import rewrite_urls


from lxml.html import parse, tostring
from pylons import tmpl_context as c, config

log = logging.getLogger(__name__)


class FileStaticPage(object):
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

_BACKENDS = {
    'filesystem': FileStaticPage,
    'database': adhocracy.model.StaticPage,
}

STATICPAGE_KEY = re.compile(r'^[a-z0-9_-]+$')


def all_locales(include_preferences=False):

    def all_locales_mult():
        if include_preferences:
            yield c.locale
            yield i18n.get_default_locale()
        for l in i18n.LOCALES:
            yield l

    done = set()

    for value in all_locales_mult():
        if value in done:
            continue
        else:
            done.add(value)
            yield value


def all_languages(include_preferences=False):
    return (l.language for l in all_locales(include_preferences))


def all_language_infos(include_preferences=False):
    return ({'id': l.language, 'name': l.display_name}
            for l in all_locales(include_preferences))


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
        for lang in all_languages(include_preferences=True):
            page = backend.get(key, lang)
            if page is not None:
                return page
        return None
    return backend.get(key, lang)


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
