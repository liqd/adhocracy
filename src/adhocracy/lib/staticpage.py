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


def all_languages(include_preferences=False):
    if include_preferences:
        yield c.locale.language
        yield i18n.get_default_locale().language
    for l in i18n.LOCALES:
        yield l.language


def all_language_infos(include_preferences=False):
    if include_preferences:
        yield {'id': c.locale.language, 'name': c.locale.display_name}
        def_locale = i18n.get_default_locale()
        yield {'id': def_locale.language, 'name': def_locale.display_name}
    for l in i18n.LOCALES:
        yield {'id': l.language, 'name': l.display_name}


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
