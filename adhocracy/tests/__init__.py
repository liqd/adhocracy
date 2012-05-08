"""Pylons application test package

This package assumes the Pylons environment is already loaded, such as
when this script is imported from the `nosetests --with-pylons=test.ini`
command.

This module initializes the application via ``websetup`` (`paster
setup-app`) and provides the base testing objects.

To guarantee test isolation make sure to use TestCaseBase.setUp() and
.tearDown() in your test case classes.
"""
from unittest import TestCase

from paste.deploy import loadapp
from paste.script.appinstall import SetupCommand

import pylons
from pylons import config, url

from routes.util import URLGenerator

from webtest import TestApp


from adhocracy.lib.app_globals import Globals
from adhocracy.model import Group, Instance, meta
from adhocracy.tests.testtools import tt_make_user


# --[ load default database and create a root transaction to roll back to ]-

def create_simple_session():
    '''
    Create a new, not scoped  global sqlalchemy session
    and rebind it to a new root transaction to which we can roll
    back. Otherwise :func:`adhocracy.model.init_model`
    will create as scoped session and invalidates
    the connection we need to begin a new root transaction.

    Return: The new root `connection`
    '''
    from sqlalchemy import engine_from_config
    from sqlalchemy.orm.session import Session

    engine = engine_from_config(config, 'sqlalchemy.')
    meta.engine = engine
    connection = engine.connect()
    meta.Session = Session(autoflush=True, bind=connection)
    return connection

connection = create_simple_session()

# Invoke websetup with the current config file
SetupCommand('setup-app').run([config['__file__']])

# create a root transaction we can use to roll back the commits
# done during the tests.
root_transaction = connection.begin()


# --[ Mock and configure context variables used by adhocracy       ]----
# --[ outside the request                                          ]----

class MockBase(object):
    '''Marker object used during cleanup'''


class MockRequest(MockBase):
    '''A mocked request'''

    def __init__(self, **kwargs):
        for arg, value in kwargs.items():
            setattr(self, arg, value)


class MockContextObject(pylons.util.ContextObj, MockBase):
    '''
    A mocked pylons :class:`pylons.util.ContextObj` object used
    by pylons, often thread local, in many cases, like pylons.tmpl_context
    '''


def _teardown_context(proxy, context_class=MockBase):
    while True:
        try:
            current = proxy._current_obj()
        except TypeError:
            # no object registered
            break
        if isinstance(current, context_class):
            proxy._pop_object()
        else:
            break


def _register_tmpl_context(instance=None, user=None, **kwargs):
    '''
    Setup thread local variables that are normally only available
    in pylons during the request.
    '''
    c = MockContextObject()
    c.instance = instance
    c.user = user
    for key in kwargs:
        setattr(c, key, kwargs[key])
    pylons.tmpl_context._push_object(c)
    return (_teardown_context, (pylons.tmpl_context))


def _unregister_tmpl_context():
    _teardown_context(pylons.tmpl_context)


def _register_request(**kwargs):
    '''
    Many library functions in adhocracy informations from
    the request, like "adhocracy.domain".

    Returns: An request object that can be removed with
    :func:`_unregister_request`.
    '''
    request = MockRequest(**kwargs)
    pylons.request._push_object(request)


def _unregister_request():
    _teardown_context(pylons.request)


def _unregister_instance():
    """
    the counterpart ot .testtool.tt_get_instance's
    call to .model.ifilter.setup_thread()
    """
    from adhocracy.model import instance_filter
    instance_filter.teardown_thread()


environ = {}


class TestControllerBase(TestCase):

    @classmethod
    def setup_class(cls):
        cls._rollback_session()

    @classmethod
    def teardown_class(cls):
        cls._rollback_session()
        _unregister_instance()

    def tearDown(self):
        self._rollback_session()

    def __init__(self, *args, **kwargs):
        if pylons.test.pylonsapp:
            wsgiapp = pylons.test.pylonsapp
        else:
            wsgiapp = loadapp('config:%s' % config['__file__'])
        self.app = TestApp(wsgiapp)
        url._push_object(URLGenerator(config['routes.map'], environ))
        # should perhaps be in setup
        pylons.app_globals._push_object(Globals())
        # pylons.app_globals._pop_object() # should perhaps be in teardown

        super(TestControllerBase, self).__init__(*args, **kwargs)

    @classmethod
    def _rollback_session(cls):
        meta.Session.rollback()
        root_transaction.rollback()


class TestController(TestControllerBase):

    # will be registered in setUp()
    request = {'environ': {'adhocracy.domain': 'test.lan',
                           'SERVER_PORT': '80'}}

    @classmethod
    def setup_class(cls):
        pass

    def setUp(self):
        super(TestController, self).setUp()
        # the test instance is generated by setup-app
        instance = Instance.find('test')
        assert instance, "We need an instance to setup the context"
        _register_tmpl_context(instance, user=None)
        _register_request(**self.request)

    def tearDown(self):
        _teardown_context(pylons.tmpl_context)
        _teardown_context(pylons.request)
        _unregister_instance()
        super(TestController, self).tearDown()


class WebTestController(TestControllerBase):

    DEFAULT = Group.CODE_DEFAULT
    OBSERVER = Group.CODE_OBSERVER
    VOTER = Group.CODE_VOTER
    SUPERVISOR = Group.CODE_SUPERVISOR

    def setUp(self):
        super(WebTestController, self).setUp()

    def tearDown(self):
        super(WebTestController, self).tearDown()

    def prepare_app(self, anonymous=False, group_code=None, instance=True):
        self.app.extra_environ = dict()
        self.user = None
        if not anonymous:
            group = None
            if group_code:
                group = Group.by_code(group_code)
            self.user = tt_make_user(instance_group=group)
            self.app.extra_environ['REMOTE_USER'] = str(self.user.user_name)
        if instance:
            self.app.extra_environ['HTTP_HOST'] = "test.test.lan"
        else:
            self.app.extra_environ['HTTP_HOST'] = "test.lan"
