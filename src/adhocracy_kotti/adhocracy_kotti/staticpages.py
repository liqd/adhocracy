"""Staticpages rest web service"""

from pyramid import traversal
from cornice import Service
from adhocracy_kotti import schemata
from adhocracy_kotti import utils

staticpages = Service(name='staticpages',
                      path='/staticpages',
                      description="Service to retrieve Kotti static pages")

staticpage = Service(name='staticpage',
                     path='/staticpages/single',
                     description="Service to retrieve a single HTML page")


def get_children_tree(node):

    return {
        'name': node.name,
        'title': node.title,
        'children': [get_children_tree(c)
                     for c in node.children
                     if c.in_navigation and c.state == u'public'],
    }


def get_staticpages(languages):

    lang = languages.pop(0)
    try:
        lang_folder = utils.get_lang_folder(lang)
        return get_children_tree(lang_folder)

    except utils.NoSuchLanguageException:
        pass

    if languages:
        return get_staticpages(languages)

    return None


@staticpages.get(schema=schemata.StaticPagesGET)
def staticpages_get(request):
    data = request.validated
    return get_staticpages(data['lang'])


def get_staticpage(path, languages):

    lang = languages.pop(0)

    try:
        lang_folder = utils.get_lang_folder(lang)
        page = traversal.find_resource(lang_folder, path)
        if page.state == u'private':
            return None
        return {
            'path': path,
            'lang': lang,
            'title': page.title,
            'description': page.description,
            'body': page.body,
            #'last_modified': page.modification_date,
        }

    except utils.NoSuchLanguageException:
        pass
    except KeyError:
        pass

    if languages:
        return get_staticpage(path, languages)
    return None


@staticpage.get(schema=schemata.StaticPageGET)
def staticpage_get(request):
    """
    Get a static page.

    Expects a list of languages.
    """
    data = request.validated
    return get_staticpage(data['path'], data['lang'])
