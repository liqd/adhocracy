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

    >>> browser.open(BASE_URL + '/edit')
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

and add a Document::

    >>> browser.getLink("Document").click()
    >>> ctrl("Title").value = "German document"
    >>> ctrl("save").click()
    >>> "Item was added" in browser.contents
    True

Now we add a translation::

    >>> browser.open("/en")
    >>> browser.url
    'http://localhost:6543/en'

    >>> browser.getLink("Document").click()
    >>> ctrl("Title").value = "English document"
    >>> ctrl("save").click()
    >>> "Item was added" in browser.contents
    True

