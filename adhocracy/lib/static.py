import os.path
from lxml.html import parse, tostring
from adhocracy import i18n
from adhocracy.lib import util
from pylons import tmpl_context as c

class FileStaticPage(object):
    def __init__(self, body, title):
        self.title = title
        self.body = body

    @staticmethod
    def create(key, lang): 
        filename = util.get_path('page', os.path.basename(key) + '.' + lang + '.html')
        try: 
            root = parse(filename)
        except IOError as e:
            return None
        try: 
            body = root.find('.//body')
        except AttributeError as e:
            return None
        body.tag = 'span'
        title = root.find('.//title').text
        return FileStaticPage(tostring(body), title)

def get_static_page(key, lang=None):
    if lang is None:
        for loc in [c.locale, i18n.get_default_locale()] + i18n.LOCALES:
            return FileStaticPage.create(key, loc.language)
    return FileStaticPage.create(key, lang)
