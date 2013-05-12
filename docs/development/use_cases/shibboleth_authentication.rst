Test authentication with Shibboleth
===================================


Setup doctest:

The following is needed if we're using the standard pytest doctest runner.

#    >>> from adhocracy.tests.test_doctest_files import globs
#    >>> locals().update(globs)

    >>> SHIB_IDP_INSTITUTION = 'Dummy Institution'
    >>> from pylons import config
    >>> config['adhocracy.login_type']='shibboleth'
    >>> config['adhocracy.shibboleth.institution']=SHIB_IDP_INSTITUTION

Configuring the config here doesn't have any effect as setup_what has already
been executed before. It's just here for documentation purpose.

    >>> config['skip_authentication']='False'

Setup some URLs:

    >>> ANY_URL = app_url + '/instance'
    >>> POST_AUTH_URL = app_url + '/shibboleth/post_auth'
    >>> REQUEST_AUTH_URL = app_url + '/shibboleth/request_auth'
    >>> SHIBBOLETH_LOGIN_URL = app_url + '/Shibboleth.sso/Login'
    >>> SHIBBOLETH_LOGOUT_URL = app_url + '/Shibboleth.sso/Logout'


We're not logged in:

    >>> def is_logged_in(browser):
    ...     return u'dashboard' in browser.contents.decode('utf-8')
    ...

    >>> browser.open(ANY_URL)
    >>> browser.status
    '200 OK'

    >>> is_logged_in(browser)
    False


After successful authentication at the Shibboleth Identity Provider (IdP),
Apache mod_shibboleth sets the appropriate HTTP headers.

    >>> def add_headers(browser, headers):
    ...     for k, v in headers.iteritems():
    ...         browser.addHeader(k, v)

    >>> hugo_headers = {
    ...     'Persistent-Id': 'https://dummy_idp!http://test.lan/shibboleth!KJOPDPm4QA7NCwTWol9p2MsQGOA=',
    ...     'shib-email': 'hugo@example.com',
    ... }

    >>> add_headers(browser, hugo_headers)

This triggers a new user registration, as there is no user which corresponds
to the given persistent_id in the HTTP headers.

On the next request to whatever page, a intermediate page with a registration
form is displayed:

    >>> def set_no_redirect(browser):
    ...     browser.mech_browser.set_handle_redirect(False)
    ...     browser.raiseHttpErrors = False

    >>> set_no_redirect(browser)

FIXME: check whether ANY_URL should be encoded
    >>> browser.open(REQUEST_AUTH_URL + '?came_from=' + ANY_URL)
    >>> browser.headers['status']
    '302 Found'
    >>> browser.headers['location']
    'http://test.lan/Shibboleth.sso/Login?target=%2Fshibboleth%2Fpost_auth%3Fcame_from%3Dhttp%253A%252F%252Ftest.lan%252Finstance'

    >>> browser.open(POST_AUTH_URL + '?came_from=' + ANY_URL)

    >>> form = browser.getForm(name='complete_registration')
    >>> username = form.getControl(name='username')
    >>> username.value = 'hugo'
    >>> email = form.getControl(name='email')
    >>> email.value
    'hugo@example.com'

At the moment, zope testbrowser doesn't take the following statements into
account on browser.submit. This is being addressed in:

https://github.com/zopefoundation/zope.testbrowser/pull/4

This is required to make the test suite happy.

    >>> browser.mech_browser.set_handle_redirect(False)
    >>> browser.raiseHttpErrors = False
    >>> form.submit()
    >>> browser.headers['status']
    '302 Found'
    >>> browser.headers['location']
    'http://test.lan/Shibboleth.sso/Logout?return=http%3A%2F%2Ftest.lan%2Finstance'
    >>> browser.open(ANY_URL)
    >>> is_logged_in(browser)
    True

Fine! Let's logout!

    >>> browser.open(app_url + '/logout')

    >>> is_logged_in(browser)
    False

Login with the same Shibboleth persistent_id:

    >>> add_headers(browser, hugo_headers)
    >>> browser.open(POST_AUTH_URL)

and see: We're logged in!

    >>> browser.open(ANY_URL)
    >>> is_logged_in(browser)
    True
