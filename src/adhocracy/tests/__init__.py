"""Pylons application test package

This package assumes the Pylons environment is already loaded, such as
when this script is imported from the `nosetests --with-pylons=etc/test.ini`
command.

This module initializes the application via ``websetup`` (`paster
setup-app`) and provides the base testing objects.

To guarantee test isolation make sure to use TestCaseBase.setUp() and
.tearDown() in your test case classes.
"""
import os
from unittest import TestCase

from decorator import decorator

from mock import patch
from nose.plugins.skip import SkipTest
from paste.deploy import loadapp
from paste.deploy.converters import asbool
from paste.script.appinstall import SetupCommand

import pylons
from pylons import url

from routes.util import URLGenerator

from webtest import TestApp


from adhocracy.lib.app_globals import Globals
from adhocracy.model import Instance, meta
from adhocracy.websetup import _setup

SetupCommand('setup-app').run([pylons.test.pylonsapp.config['__file__']])


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


def is_integrationtest():
    '''
    Raise SkipTest if external services required by adhocracy
    are not present.
    '''
    from pylons import config
    if asbool(os.environ.get('ADHOCRACY_RUN_INTEGRATION_TESTS', 'false')):
        return # Run the tests in any case if environment variable is set
    if not asbool(config.get('run_integrationtests', 'false')):
        raise SkipTest('This test needs all services adhocracy depends on. '
                       'If they are running and configured in test.ini '
                       'enable the tests there with '
                       '"run_integrationtests = true".')


@decorator
def integrationtest(func, *args, **kwargs):
    '''
    Decorator for tests that require external services like
    solr or redis/rq.
    '''
    is_integrationtest()
    return func(*args, **kwargs)


environ = {}


class TestControllerBase(TestCase):

    @classmethod
    def setup_class(cls):
        cls._rollback_session()

    @classmethod
    def teardown_class(cls):
        cls._rollback_session()
        _unregister_instance()

    def setUp(self):
        # mock the mail.send() function. Make sure to stop()
        # the patcher in tearDown.
        self.patcher = patch('adhocracy.lib.mail.send')
        self.mocked_mail_send = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self._rollback_session()
        meta.Session.remove()

    def __init__(self, *args, **kwargs):
        if pylons.test.pylonsapp:
            wsgiapp = pylons.test.pylonsapp
        else:
            wsgiapp = loadapp('config:%s' % config['__file__'])
        config = wsgiapp.config
        self.app = TestApp(wsgiapp)
        url._push_object(URLGenerator(config['routes.map'], environ))
        # should perhaps be in setup
        pylons.app_globals._push_object(Globals(config))
        # pylons.app_globals._pop_object() # should perhaps be in teardown

        super(TestControllerBase, self).__init__(*args, **kwargs)

    @classmethod
    def _rollback_session(cls):
        meta.Session.rollback()


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
