adhocracy staticpages REST-API browser tests
============================================

Setup
-----

    >>> import json
    >>> import pytest
    >>> from webtest import AppError
    >>> from adhocracy_kotti.testing import setup_functional, asset, API_TOKEN, BASE_URL

    >>> tools = setup_functional()
    >>> app = tools["test_app"]
    >>> browser = tools["browser"]
    >>> ctrl = browser.getControl

Login Kotti
-----------

    >>> browser.open(BASE_URL + '/login')
    >>> ctrl("Username or email").value = "admin"
    >>> ctrl("Password").value = "secret"
    >>> ctrl(name="submit").click()
    >>> "Welcome, Administrator" in browser.contents
    True

Create and Pages and translations with Kotti
---------------------------------------------

First we go to the right language folder::

    >>> browser.open("/de")
    >>> browser.url
    'http://localhost:6543/de'

to add some Documents::

    >>> browser.getLink("Document").click()
    >>> ctrl("Title").value = "Document de"
    >>> ctrl("save").click()
    >>> "alert-succes" in browser.contents
    True

    >>> browser.open("/de/document-de"))
    >>> browser.getLink("Document").click()
    >>> ctrl("Title").value = "Child Document de"
    >>> ctrl("save").click()
    >>> "alert-succes" in browser.contents
    True

Now we add a translation::

    >>> browser.open("/en")
    >>> browser.url
    'http://localhost:6543/en'

    >>> browser.getLink("Document").click()
    >>> ctrl("Title").value = "Document en"
    >>> ctrl("save").click()
    >>> "alert-succes" in browser.contents
    True


Use the restapi to retrieve Pages
----------------------------------

We can get all documents from the medicenter::

    >>> resp = app.get("/staticpages", {"lang": "de", "lang_fallbacks": '["en", "fr"]'})
    >>> resp.status
    '200 OK'

    >>> json.loads(resp.body)
    [{u"name": u"document-de", u"title": u"Document de", u"description": u"", "lang": "de"},
     {u"name": u"document-de/child-document-de", u"title": u"Child Document de", u"description": u"", "lang": "de"}]

TODO ist Seitenstruktur in allen Sprachen identisch oder nicht?  Bekommt man als Fallback nur eine Sprache?

to choose one we want the body from::

    >>> resp = app.get("/staticpages/document-de", {"lang": "de", "lang_fallback": '["en", "fr"]' })
    >>> json.loads(resp.body)
    [{u"name": u"document-de", u"title": u"Document de", u"description": u"", body=u""}, "lang":"de"]

If the language folder does not exists, we get the fallback::

    >>> resp = app.get("/staticpages/document-de", {"lang": "unknown", "lang_fallback": '["en", "fr"]'})
    >>> json.loads(resp.body)
    [{u"name": u"document-en", u"title": u"Document en", u"description": u"", body=u"", "lang":"en"}]


TODO: how to handle relative links

FUTURE: Fallback Fallback languages
