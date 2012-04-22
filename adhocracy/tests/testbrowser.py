"""Helper classes to allow function testing with a testbrowser"""
import os.path
from paste.deploy import loadapp
import zope.testbrowser.wsgi
from repoze.tm import TM
import adhocracy


class Browser(zope.testbrowser.wsgi.Browser):
    """Simplify zope.testbrowser sessions"""

    def dc(self, filename="/tmp/test-output.html"):
        open(filename, 'w').write(self.contents)


class AdhocracyAppLayer(zope.testbrowser.wsgi.Layer):
    """Layer to setup the WSGI app"""

    def make_wsgi_app(self):
        config_path = os.path.join(adhocracy.__path__[0] + '/..' + '/test.ini')
        app = loadapp('config:' + config_path)
        app = zope.testbrowser.wsgi.AuthorizationMiddleware(app)
        app = TM(app)
        return app

    def setUp(test, *args, **kwargs):
        print(
            "\n--------------------------------------------------------------"
            "\n--- Setting up database test environment, please stand by. ---"
            "\n--------------------------------------------------------------"
            "\n")
        #TODO start solr and co

    def tearDown(self, test):
        pass


ADHOCRACY_LAYER = AdhocracyAppLayer()
ADHOCRACY_LAYER_APP = ADHOCRACY_LAYER.make_wsgi_app()
