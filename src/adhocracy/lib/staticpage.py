import logging
import os.path
import re

from lxml.html import parse, tostring
import adhocracy.model
from adhocracy import i18n
from adhocracy.lib import util
from adhocracy.lib.auth.authorization import has

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
            logging.debug(u'Failed to parse static document ' + filename)
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


class all_locales(object):

    def __init__(self, include_preferences=False):
        self.done = set([])
        self.include_preferences = include_preferences
        self.locales = self.next_locales()

    def __iter__(self):
        return self

    def next(self):
        value = self.locales.next()
        if value in self.done:
            return self.next()
        else:
            self.done.add(value)
            return value

    def next_locales(self):
        if self.include_preferences:
            yield c.locale
            yield i18n.get_default_locale()
        for l in i18n.LOCALES:
            yield l


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


def get_static_page(key, language=None):
    backend = get_backend()
    if language is None:
        for lang in all_languages(include_preferences=True):
            page = backend.get(key, lang)
            if page is not None:
                return page
        return None
    return backend.get(key, lang)
