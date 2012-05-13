Test basic functionality in the page root
=========================================

Make (reasonably) sure that we have a clean environment::

    >>> model.User.all()
    [<User(1,admin)>]

Call the root

   >>> browser.open(app_url)
   >>> browser.status
   '200 OK'

We have a login link on the start page

    >>> '%s/login' %app_url in browser.contents
    True 
    >>> browser.getLink('Login').click()
    >>> browser.getControl(name='login')
    <Control name='login' type='text'>
    >>> browser.getControl(name='password')
    <Control name='password' type='password'>

And an rss link

    >>> browser.open(app_url)
    >>> browser.xpath("//link[@href='http://test.lan/feed.rss']")
    [<Element link at ...>]
