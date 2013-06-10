"""
This script imports static pages from an adhocracy instance to a kotti
staticpage backend.

Note: This needs to be run within the proper adhocracy environment, e.g. by
calling it from within a paster environment:

    bin/paster shell etc/adhocracy.ini

And from there:

    from scripts import import_to_kotti
    import_to_kotti.main()
"""

import re
import sys

from bs4 import BeautifulSoup
from kotti.resources import DBSession
from kotti.resources import Document
from kotti.workflow import get_workflow
from pyramid_tm import transaction
import requests

from adhocracy_kotti.utils import get_lang_folder


# Configuration

SERVER_URL = u'https://adhocracy.de'
PAGE_PREFIX = u'/_pages'
TARGET_LANG = u'de'
OVERWRITE = True
VERIFY_SSL = True

_visited = set()


def main():

    transaction.begin()

    # Open any document to get the documents from the navigation
    page = BeautifulSoup(
        requests.get(SERVER_URL + '/instance', verify=VERIFY_SSL).content)

    target = get_lang_folder(TARGET_LANG)

    for li in get_main_nav_items(page):
        add_document(target, li)

    add_remaining_pages(target, page)

    transaction.commit()


def get_main_nav_items(page):

    return filter(
        lambda li: li.get('id') not in [u'nav_home',
                                        u'nav_instances',
                                        u'nav_login'],
        page.find(id='nav').find('div', class_='menu').ul.find_all(
            'li', recursive=False))


def get_or_create(target, slug, public=True, in_navigation=True):

    if slug in target:
        doc = target[slug]
    else:
        doc = Document()
        target[slug] = doc

    DBSession.flush()  # Initializes workflow

    if public:
        wf = get_workflow(doc)
        wf.transition_to_state(doc, None, u'public')
    if not in_navigation:
        doc.in_navigation = False

    return doc


def add_remaining_pages(target, page):

    misc = get_or_create(target, u'misc', public=False, in_navigation=False)
    misc.title = u'misc'

    for a in page.find_all('a'):
        if 'href' in a.attrs and a.attrs['href'].startswith(PAGE_PREFIX):
            add_document(misc, a)


def add_document(target, elem, recursive=True):

    if elem.name == u'a':
        a = elem
    else:
        a = elem.find('a', recursive=False)

    if not a:
        return

    print("checking %s ..." % a)
    if not 'href' in a.attrs:
        return

    url = make_url(a.attrs['href'])

    if url in _visited:
        return
    _visited.add(url)

    slug = a.attrs['href'].rstrip('/').rsplit('/')[-1]

    page = BeautifulSoup(requests.get(url, verify=VERIFY_SSL).content)
    body = page.find(id='col1_content').decode_contents()

    if (slug not in target) or OVERWRITE:

        doc = get_or_create(target, slug)
        doc.title = a.text
        doc.body = body

    if recursive:
        children = elem.find('ul', class_='children')
        if children is not None:
            for child in children.find_all('li'):
                add_document(target[slug], child)


def make_url(href):
    if re.match('^https?://.*', href):
        # FQDN
        return href
    elif re.match('^/.*', href):
        # Absolute link
        return SERVER_URL + href
    else:
        # Relative link
        raise NotImplemented


if __name__ == '__main__':
    sys.exit(main())
