import base64
import logging
import os.path
import re

import adhocracy.model
from adhocracy import i18n
from adhocracy.lib import util
from adhocracy.lib.auth.authorization import has
from adhocracy.lib.crypto import sign, verify

import lxml.etree
from lxml.html import parse, tostring
from paste.deploy.converters import asbool
from pylons import tmpl_context as c, config

log = logging.getLogger(__name__)

REDIRECT_SALT = b'static link'


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


def get_static_page(key, language=None):
    backend = get_backend()
    if language is None:
        for lang in all_languages(include_preferences=True):
            page = backend.get(key, lang)
            if page is not None:
                return page
        return None
    return backend.get(key, lang)


def render_body(body):
    from adhocracy.lib.helpers import base_url
    if not asbool(config.get('adhocracy.track_outgoing_links', 'False')):
        return body

    doc = lxml.etree.fromstring('<body>' + body + '</body>')
    for a in doc.xpath('.//a[@href]'):
        if re.match(r'ftps?:|https?:|//', a.attrib['href']):
            url = a.attrib['href']
            encoded_url = base64.urlsafe_b64encode(url.encode('utf-8'))
            signed_url = sign(encoded_url, salt=REDIRECT_SALT)
            redirect_url = u'/outgoing_link/' + signed_url.decode('utf-8')
            a.attrib['href'] = base_url(redirect_url)
    res = lxml.etree.tostring(doc)
    return res[len(b'<body>'):-len(b'</body>')]


def decode_redirect(signed_url):
    encoded_url = verify(signed_url.encode('utf-8'), salt=REDIRECT_SALT)
    url = base64.urlsafe_b64decode(encoded_url).decode('utf-8')
    return url
