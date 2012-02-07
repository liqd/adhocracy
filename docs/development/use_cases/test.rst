
testbrowser example
===================


We can open the adhocracy startpage and write the response html to /tmp/test-output.html::

    >>> browser.open(app_url + "/login")
    >>> browser.dc()
    >>> browser.url
    'http://localhost/login'
