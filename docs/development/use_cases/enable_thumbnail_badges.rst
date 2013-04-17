Enable thumbnail badges
=======================

As a global administrator:


    >>> admin = make_browser()
    >>> admin.login('admin')
    >>> admin.open('http://test.lan/')

Go to the instance settings form:

    >>> admin.open('http://test.test.lan/instance/test/settings/contents')

Enable thumbnail badges

    >>> form = admin.getForm(name='create_instance')
    >>> form.getControl(name='allow_thumbnailbadges').value = True
    >>> form.submit()
