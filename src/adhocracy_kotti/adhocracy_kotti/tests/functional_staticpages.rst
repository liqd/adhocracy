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
    >>> ctrl("Title").value = "Document"
    >>> ctrl("Body").value = "Dokument auf deutsch"
    >>> ctrl("save").click()
    >>> "alert-succes" in browser.contents
    True

    >>> browser.open("/de/document")
    >>> browser.getLink("Document").click()
    >>> ctrl("Title").value = "Child Document"
    >>> ctrl("save").click()
    >>> "alert-succes" in browser.contents
    True

Now we add a translation::

    >>> browser.open("/en")
    >>> browser.url
    'http://localhost:6543/en'

    >>> browser.getLink("Document").click()
    >>> ctrl("Title").value = "Document"
    >>> ctrl("Body").value = "Document in English"
    >>> ctrl("save").click()
    >>> "alert-succes" in browser.contents
    True


Use the restapi to retrieve Pages
----------------------------------

We can get all documents from through the API::

    >>> resp = app.get("/staticpages?lang=de&lang=en")
    >>> resp.status
    '200 OK'

    >>> json.loads(resp.body)
    {u'title': u'DE translations', u'children': [{u'title': u'Mainmenu', u'children': [], u'name': u'mainmennu'}, {u'title': u'Footer', u'children': [], u'name': u'footer'}, {u'title': u'Document', u'children': [{u'title': u'Child Document', u'children': [], u'name': u'child-document'}], u'name': u'document'}], u'name': u'de'}


to choose one we want the body from::

    >>> resp = app.get("/staticpages/document?lang=de&lang=en&lang=fr")
    >>> json.loads(resp.body)
    {u'lang': u'de', u'path': u'document', u'body': u'Dokument auf deutsch', u'description': u'', u'title': u'Document'}

If the language folder does not exists, we get the fallback::

    >>> resp = app.get("/staticpages/document?lang=fr&lang=en&lang=de")
    >>> json.loads(resp.body)
    {u'lang': u'en', u'path': u'document', u'body': u'Document in English', u'description': u'', u'title': u'Document'}


TODO: how to handle relative links
