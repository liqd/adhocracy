from pytest import fixture
from webtest import TestApp
from kotti import base_configure
from kotti.tests import (
    settings,
)


@fixture
def testapp(db_session, request):
    """returns an instance of webtest.TestApp"""

    wsgi_app = base_configure({}, **settings()).make_wsgi_app()
    testapp = TestApp(wsgi_app)
    return testapp
