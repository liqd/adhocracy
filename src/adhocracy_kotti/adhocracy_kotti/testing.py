from os.path import (
    join,
    dirname
)

BASE_URL = 'http://localhost:6543'


API_TOKEN = 'evqTj3ucH'


def asset(name):
    import adhocracy_kotti
    return open(join(dirname(adhocracy_kotti.__file__), 'tests', name), 'rb')


def setup_functional(global_config=None, **settings):
    from kotti import main
    from kotti.testing import tearDown
    import wsgi_intercept.zope_testbrowser
    from webtest import TestApp

    tearDown()

    # TODO more DRY, use tests.conftest.settings
    _settings = {
        'sqlalchemy.url': "sqlite://",
        'kotti.secret': 'secret',
        'kotti.populators': 'adhocracy_kotti.populate.populate',
        'pyramid.includes': 'kotti.testing._functional_includeme '
                            'adhocracy_kotti',
        'kotti.configurators': 'kotti_tinymce.kotti_configure '
                               'adhocracy_kotti.kotti_configure',
        'rest_api_token': API_TOKEN,
    }
    _settings.update(settings)

    host, port = BASE_URL.split(':')[-2:]
    app = main({}, **_settings)
    wsgi_intercept.add_wsgi_intercept(host[2:], int(port), lambda: app)
    Browser = wsgi_intercept.zope_testbrowser.WSGI_Browser

    return dict(
        Browser=Browser,
        browser=Browser(),
        test_app=TestApp(app),
        )
