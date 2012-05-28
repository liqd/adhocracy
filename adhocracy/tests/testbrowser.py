"""Helper classes to allow function testing with a testbrowser"""

from lxml import etree
from lxml.cssselect import CSSSelector

from mock import patch

from pylons import config
from pylons.test import pylonsapp
from repoze.tm import TM
import zope.testbrowser.wsgi

from adhocracy.model import meta
from adhocracy.lib.search import drop_all, rebuild_all
from adhocracy import tests

adhocracy_domain = config.get('adhocracy.domain').strip()
app_url = "http://%s" % adhocracy_domain
instance_url = "http://test.%s" % adhocracy_domain


class Browser(zope.testbrowser.wsgi.Browser):
    """Simplify zope.testbrowser sessions"""

    REMOTE_USER_HEADER = 'REMOTE_USER'

    app_url = app_url
    instance_url = instance_url

    def dc(self, filename="/tmp/test-output.html"):
        open(filename, 'w').write(self.contents)

    def login(self, username):
        self.logout()
        # 'REMOTE_USER' will turn into HTTP_REMOTE_USER in the wsgi environ.
        self.addHeader(self.REMOTE_USER_HEADER, username)

    def logout(self):
        self.mech_browser.addheaders = [header for header in
                                        self.mech_browser.addheaders if
                                        header[0] != self.REMOTE_USER_HEADER]

    @property
    def status(self):
        return self.headers['Status']

    def etree(self):
        '''
        return an lxml.etree from the contents.
        '''
        return etree.fromstring(self.contents)

    def cssselect(self, selector):
        cssselector = CSSSelector(selector)
        return cssselector(self.etree())

    def xpath(self, selector):
        return self.etree().xpath(selector)


class AdhocracyAppLayer(zope.testbrowser.wsgi.Layer):
    """Layer to setup the WSGI app"""

    def make_wsgi_app(self):
        app = pylonsapp
        app = zope.testbrowser.wsgi.AuthorizationMiddleware(app)
        app = TM(app)
        zope.testbrowser.wsgi._allowed.add(adhocracy_domain)
        zope.testbrowser.wsgi._allowed_2nd_level.add(adhocracy_domain)
        return app

    def setUp(test, *args, **kwargs):
        # we skip this test if we don't have a full stack
        # test environment
        tests.is_integrationtest()

        connection = meta.engine.connect()
        test.trans = connection.begin()
        meta.Session.configure(bind=connection)
        # delete and reindex solr
        drop_all()
        rebuild_all()

        # mock the mail.send() function. Make sure to stop()
        # the patcher in tearDown.
        test.patcher = patch('adhocracy.lib.mail.send')
        test.mocked_mail_send = test.patcher.start()
        #TODO start solr and co

    def tearDown(self, test):
        self.trans.rollback()
        self.patcher.stop()
        meta.Session.close()


ADHOCRACY_LAYER = AdhocracyAppLayer()
ADHOCRACY_LAYER_APP = ADHOCRACY_LAYER.make_wsgi_app()
