testbrowser example
===================


Make (reasonably) sure that we have a clean environment::

    >>> model.User.all()
    [<User(1,admin)>]

We have a testbrowser `browser` set up that we can use to browse throug the 
site::

    >>> browser.open(app_url + "/login")
    >>> browser.dc()
    >>> browser.status
    '200 OK'
    >>> '<html class="no-js">' in browser.contents
    True

`browser.dc('/path/to/file')` would dump the current html to a file.

We can also instanciate a new browser and login as a certain user::

    >>> admin_browser = make_browser()
    >>> admin_browser.open(app_url)
    >>> 'http://test.lan/user/admin/dashboard' in admin_browser.contents
    False
    >>> admin_browser.login('admin')
    >>> admin_browser.open(app_url)
    >>> 'http://test.lan/user/admin/dashboard' in admin_browser.contents
    True

And we can log out.

    >>> admin_browser.logout()
    >>> admin_browser.open(app_url)
    >>> 'http://test.lan/user/admin/dashboard' in admin_browser.contents
    False

This won't affect our first browser::

    >>> browser.url
    'http://test.lan/login'
