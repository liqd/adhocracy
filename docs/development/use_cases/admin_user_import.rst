Mass import users
=================

As a global administrator:


    >>> admin = make_browser()
    >>> admin.login('admin')
    >>> admin.open('http://test.lan/admin')

Open and fill out the *Import Users* form:

    >>> admin.follow('Import Users')
    >>> admin.url
    'http://test.lan/admin/users/import'
    >>> csv = admin.getControl(name='users_csv')
    >>> csv.value = ('testuser,"Test User",testuser@example.com\n'
    ...              'testuser2,"Test User2",testuser2@example.com')
    >>> admin.getControl(name='email_subject').value = 'hello new user'
    >>> template = admin.getControl(name='email_template')
    >>> template.value = ('{user_name}\n{password}\n{url}\n'
    ...                   '{display_name}\n{email}\nFree Text')
    >>> admin.getControl('save').click()

As a result we have two new users and sent out emails to them:

    >>> model.User.all()
    [<User(1,admin)>, <User(2,testuser)>, <User(3,testuser2)>]
    >>> self.mocked_mail_send.assert_any_call(mock.ANY, 'testuser@example.com', mock.ANY)
    >>> self.mocked_mail_send.assert_any_call(mock.ANY, 'testuser2@example.com', mock.ANY)

Anonymous users cannot open the form:

    >>> anon = make_browser()
    >>> anon.handleErrors = True
    >>> anon.raiseHttpErrors = False
    >>> anon.open('http://test.lan/admin/users/import')
    >>> anon.status
    '401 Unauthorized'
