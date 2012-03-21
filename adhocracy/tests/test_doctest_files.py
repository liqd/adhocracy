import doctest
from doctest import DocFileSuite
import unittest
from adhocracy.tests.testbrowser import ADHOCRACY_LAYER
from adhocracy.tests.testbrowser import ADHOCRACY_LAYER_APP
from adhocracy.tests.testbrowser import Browser


flags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
globs = {"browser" : Browser(wsgi_app=ADHOCRACY_LAYER_APP),
         "app"     :  ADHOCRACY_LAYER_APP,
         "app_url" : "http://localhost",
        }


class DoctestTestCase(unittest.TestCase):

    def __new__(self, test):
        return getattr(self, test)()

    @classmethod
    def test_suite(self):
        return DocFileSuite(
            "use_cases/test.rst",
            #add here aditional testfiles
            setUp = ADHOCRACY_LAYER.setUp,
            tearDown = ADHOCRACY_LAYER.tearDown,
            globs = globs,
            optionflags = flags
        )
