from glob import glob
import doctest
from doctest import DocFileSuite
from os.path import dirname
import unittest

from adhocracy.tests.testbrowser import ADHOCRACY_LAYER
from adhocracy.tests.testbrowser import ADHOCRACY_LAYER_APP
from adhocracy.tests.testbrowser import Browser


def find_use_cases():
    here = dirname(__file__)
    paths = glob('{here}/use_cases/*.rst'.format(here=here))
    # we need relative paths for DocFileSuite
    pathes = [path.replace(here, '.') for path in paths]
    return pathes


flags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
globs = {"browser": Browser(wsgi_app=ADHOCRACY_LAYER_APP),
         "app":  ADHOCRACY_LAYER_APP,
         "app_url": "http://localhost",
        }
use_cases = find_use_cases()


class DoctestTestCase(unittest.TestCase):

    def __new__(self, test):
        return getattr(self, test)()

    @classmethod
    def test_suite(self):
        return DocFileSuite(
            *use_cases,
            #add here aditional testfiles
            setUp=ADHOCRACY_LAYER.setUp,
            tearDown=ADHOCRACY_LAYER.tearDown,
            globs=globs,
            optionflags=flags
        )
