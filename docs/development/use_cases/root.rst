Test basic functionality in the page root
=========================================

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

Break the following tests::

#   >>> testtools.tt_make_user('voter')
#   <User(2,voter)>
