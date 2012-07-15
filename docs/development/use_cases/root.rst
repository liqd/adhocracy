Test basic functionality in the page root
=========================================

Make (reasonably) sure that we have a clean environment::

    >>> model.User.all()
    [<User(1,admin)>]

Call the root

   >>> browser.open(app_url)
   >>> browser.status
   '200 OK'


Login Form
==========

We have a login link on the start page

    >>> '%s/login' %app_url in browser.contents
    True 
    >>> browser.getLink('Login').click()
    >>> browser.getControl(name='login')
    <Control name='login' type='text'>
    >>> browser.getControl(name='password')
    <Control name='password' type='password'>


RSS feed
========

Adhocracy has a global rss feed showing events in all instances::

    >>> browser.open(app_url)
    >>> browser.xpath("//link[@href='http://test.lan/feed.rss']")
    [<Element link at ...>]
    >>> browser.open('http://test.lan/feed.rss')
    >>> browser.open('http://test.lan/feed.rss')
    >>> browser.headers['Content-Type']
    'application/rss+xml; charset=utf-8'

We have no items in the rss feed yet::

    >>> len(browser.xpath('//item'))
    0

If we add content in the test instance the feed contains an item
for the event::

    >>> admin = make_browser()
    >>> admin.login('admin')
    >>> admin.open(instance_url)
    >>> admin.follow('Proposals')
    >>> admin.follow('new proposal')
    >>> form = admin.getForm(name='create_proposal')
    >>> form.getControl(name='label').value = u'Test Proposal'
    >>> form.getControl(name='text').value = u'Test Description'
    >>> form.submit()
    >>> browser.open('http://test.lan/feed.rss')
    >>> browser.url
    'http://test.lan/feed.rss'
    >>> len(browser.xpath('//item'))
    1

    >>> admin.open(instance_url)
    >>> admin.follow('Proposals')
    >>> admin.follow('new proposal')
    >>> form = admin.getForm(name='create_proposal')
    >>> form.getControl(name='label').value = u'Test Proposal 2'
    >>> form.getControl(name='text').value = u'Test Description 2'
    >>> form.submit()
    >>> browser.open('http://test.lan/feed.rss')
    >>> browser.url
    'http://test.lan/feed.rss'
    >>> len(browser.xpath('//item'))
    2



