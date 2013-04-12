from pytest import fixture
from webtest import TestApp
from kotti import base_configure
from cornice.errors import Errors


def settings():
    from kotti import _resolve_dotted
    from kotti import conf_defaults
    settings = conf_defaults.copy()
    settings['kotti.secret'] = 'secret'
    settings['kotti.populators'] =\
        'adhocracy_kotti.populate.populate'
    settings['pyramid.includes'] = 'adhocracy_kotti'
    _resolve_dotted(settings)
    return settings


@fixture
def dummy_request(config):
    """ returns a dummy request object after registering it as
        the currently active request.  This is needed when
        `pyramid.threadlocal.get_current_request` is used.
    """
    from kotti.testing import DummyRequest
    config.manager.get()['request'] = request = DummyRequest()
    request.errors = Errors(request)
    return request


@fixture
def populate(db_session, content):
    """run adhocracy_kotti.populate to create initial content"""

    from adhocracy_kotti.populate import populate
    from kotti import DBSession
    from kotti.resources import Document
    import transaction
    # undo the default testing populator
    for doc in DBSession.query(Document):
        DBSession.delete(doc)
    # create initial content
    populate()
    transaction.commit()


@fixture
def testapp(populate):
    """returns an instance of webtest.TestApp"""

    wsgi_app = base_configure({}, **settings()).make_wsgi_app()
    testapp = TestApp(wsgi_app)
    return testapp
