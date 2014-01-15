import logging
import os.path
import re

import adhocracy.model
from adhocracy import i18n
from adhocracy.lib.helpers.adhocracy_service import RESTAPI
from adhocracy.lib import util
from adhocracy.lib.auth import require
from adhocracy.lib.auth.authorization import has
from adhocracy.lib.outgoing_link import rewrite_urls


from lxml.html import parse, tostring
from pylons import config

log = logging.getLogger(__name__)


class StaticPageBase(object):

    def __init__(self, key, lang, body, title, private=False,
                 nav=u'', description=u'', column_right=u'', css_classes=[],
                 redirect_url=u''):
        self.key = key
        self.lang = lang
        self.title = title
        self.body = body
        self.private = private
        self.nav = nav
        self.description = description
        self.column_right = column_right
        self.css_classes = css_classes
        self.redirect_url = redirect_url

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

    def require_permission(self):
        """
        Backends can add additional permission checks.
        """
        if self.private:
            require.perm('static.show_private')


class FileStaticPage(StaticPageBase):

    @staticmethod
    def get(key, languages):

        for lang in languages:
            fn = key + '.' + lang + '.html'
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


class ExternalStaticPage(StaticPageBase):

    @staticmethod
    def get(key, languages):
        api = RESTAPI()
        result = api.staticpage_get(key)
        page = result.json()
        if page is None or 'errors' in page:
            return None
        data = {'lang': u'',
                'title': u'',
                'description': u'',
                'body': u'',
                'column_right': u'',
                'nav': u'',
                'css_classes': [],
                'private': False,
                'redirect_url': u'',
                }
        data.update(page)
        return ExternalStaticPage(key, **data)

_BACKENDS = {
    'filesystem': FileStaticPage,
    'database': adhocracy.model.StaticPage,
    'external': ExternalStaticPage,
}

STATICPAGE_KEY = re.compile(r'^[a-z0-9_\-/]+$')


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
    if page is not None:
        page.require_permission()
    return page


def add_static_content(data, config_key, title_key=u'title',
                       body_key=u'body', css_classes_key=u'css_classes'):

    static_path = config.get(config_key)
    if static_path is not None:
        page = get_static_page(static_path)
        if page is None:
            data[title_key] = data[body_key] = None
        else:
            data[title_key] = page.title
            data[body_key] = render_body(page.body)
            data[css_classes_key] = page.css_classes
    else:
        data[title_key] = data[body_key] = None
