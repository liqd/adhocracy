from pytest import fixture
from webtest import TestApp
from kotti import base_configure


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
