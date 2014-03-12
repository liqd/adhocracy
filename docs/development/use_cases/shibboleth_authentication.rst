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
    >>> config['adhocracy.shibboleth.email']='register'
    >>> config['adhocracy.shibboleth.userbadge_mapping']="""[
    ...     {
    ...        "title": "editor",
    ...        "function": "attribute_equals",
    ...        "args": {"key": "shib-user-role", "value": "editor"}
    ...     },
    ...     {
    ...         "title": "staff",
    ...         "function": "attribute_equals",
    ...         "args": {"key": "shib-user-role", "value": "staff"}
    ...     }]
    ... """

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
    ...     'shib-user-role': 'editor',
    ... }

    >>> add_headers(browser, hugo_headers)

This triggers a new user registration, as there is no user which corresponds
to the given persistent_id in the HTTP headers.

On the next request to whatever page, a intermediate page with a registration
form is displayed:

    >>> def set_redirect(browser, bool):
    ...     browser.mech_browser.set_handle_redirect(bool)
    ...     browser.raiseHttpErrors = bool

    >>> set_redirect(browser, False)

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

Check that the user exists in the database and has the right user badges set:

    >>> from adhocracy.model import User
    >>> hugo = User.find('hugo')
    >>> hugo.email
    u'hugo@example.com'
    >>> hugo.badges
    [<UserBadge(1,editor)>]

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

Logout again.

    >>> browser.open(app_url + '/logout')
    >>> is_logged_in(browser)
    False

Hugo has lost his `editor` status. Make sure the model is updated.

    >>> new_hugo_headers = {
    ...     'Persistent-Id': 'https://dummy_idp!http://test.lan/shibboleth!KJOPDPm4QA7NCwTWol9p2MsQGOA=',
    ...     'shib-email': 'hugo@example.com',
    ... }
    >>> browser2 = make_browser()
    >>> set_redirect(browser2, False)
    >>> add_headers(browser2, new_hugo_headers)
    >>> browser2.open(POST_AUTH_URL + '?came_from=' + ANY_URL)
    >>> browser2.open(ANY_URL)
    >>> is_logged_in(browser2)
    True

    >>> from adhocracy.model import User
    >>> hugo = User.find('hugo')
    >>> hugo.email
    u'hugo@example.com'
    >>> hugo.badges
    []


In another scenario, users should inherit even more attributes from the
shibboleth IdP:

    >>> config.update({
    ...     'adhocracy.force_randomized_user_names': 'true',
    ...     'adhocracy.shibboleth.email': 'register',
    ...     'adhocracy.shibboleth.display_name.function': """
    ...         {
    ...             "function": "full_name",
    ...             "args": {
    ...                 "name_attr": "shib-name",
    ...                 "surname_attr": "shib-surname"
    ...             }
    ...         }
    ...     """,
    ...     'adhocracy.shibboleth.locale.attribute': 'shib-locale',
    ...     'adhocracy.shibboleth.register_form': 'false',
    ...     'adhocracy.shibboleth.userbadge_mapping': """
    ...         {}
    ...     """
    ... })

voter main attribute_equals shib-user-role voter
voter intern attribute_equals shib-user-role voter

    >>> browser = make_browser()
    >>> browser.open(ANY_URL)
    >>> is_logged_in(browser)
    False


Let's login as another user:

    >>> set_redirect(browser, False)
    >>> browser.open(REQUEST_AUTH_URL + '?came_from=' + ANY_URL)

Simulate IdP behavior:

    >>> paula_headers = {
    ...     'Persistent-Id': 'https://dummy_idp!http://test.lan/shibboleth!ohyiez0akahjielahng4Mei9Hk4=',
    ...     'shib-email': 'paula@example.com',
    ...     'shib-user-role': 'voter',
    ...     'shib-locale': 'de',
    ...     'shib-name': 'Paula',
    ...     'shib-surname': 'Frank',
    ... }

    >>> add_headers(browser, paula_headers)
    >>> browser.open(POST_AUTH_URL + '?came_from=' + ANY_URL)
    >>> browser.status
    '302 Found'
    >>> browser.headers["location"]
    'http://test.lan/Shibboleth.sso/Logout?return=http%3A%2F%2Ftest.lan%2Finstance'
    >>> browser.open(ANY_URL)

    >>> is_logged_in(browser)
    True

    >>> set_redirect(browser, True)
    >>> browser.open(app_url + '/user/redirect_settings')

    >>> u"Paula Frank" in unicode(browser.contents, errors = 'replace')
    True

    >>> form = browser.getForm(index=0)
    >>> locale = form.getControl(name='locale')
    >>> locale.value
    ['de_DE']

    >>> a = browser.getLink('Benachrichtigungen')
    >>> a.click()

    >>> u"paula@example.com" in unicode(browser.contents, errors = 'replace')
    True
