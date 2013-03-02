import logging
import os.path
from lxml.html import parse, tostring
from adhocracy import i18n
from adhocracy.lib import util
from pylons import tmpl_context as c

log = logging.getLogger(__name__)

class FileStaticPage(object):
    def __init__(self, body, title):
        self.title = title
        self.body = body

    @staticmethod
    def create(key, lang):
        filename = util.get_path('page', os.path.basename(key) + '.' + lang + '.html')
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
        return FileStaticPage(tostring(body), title)

def get_static_page(key, language=None):
    if language is None:
        for locale in [c.locale, i18n.get_default_locale()] + i18n.LOCALES:
            page = FileStaticPage.create(key, locale.language)
            if page is not None:
                return page
        return None
    return FileStaticPage.create(key, lang)
