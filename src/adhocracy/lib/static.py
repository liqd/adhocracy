import re
import os.path

from lxml.html import parse, tostring
from pylons import tmpl_context as c
from pylons.i18n import _

from adhocracy import i18n
from adhocracy.lib import util


class StaticPage(object):
    VALID_PAGE = re.compile("^[a-zA-Z0-9\_\-]*$")
    DIR = 'page'
    SUFFIX = '.html'

    def __init__(self, name):
        self.exists = False
        self.title = _("Missing page: %s") % name
        self.body = ""
        self.name = name
        if self.VALID_PAGE.match(name):
            self.lookup()

    def lookup(self):
        for locale in [c.locale, i18n.get_default_locale()] + i18n.LOCALES:
            loaded = self._lookup_lang(locale.language)
            if loaded is not None:
                break

    def _lookup_lang(self, lang):
        fmt = self.name + '.%s' + self.SUFFIX
        path = util.get_path(self.DIR, fmt % lang)
        if path is not None and os.path.exists(path):
            return self._load(path)
        return None

    def _load(self, path):
        root = parse(path)
        body = root.find('.//body')
        body.tag = 'span'
        self.body = tostring(body).encode('utf-8')
        self.title = root.find('.//title').text
        self.exists = True
        return self.title
