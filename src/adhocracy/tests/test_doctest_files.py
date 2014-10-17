from glob import glob
import doctest
from doctest import DocFileTest
from os.path import dirname

import mock

from adhocracy import model
from adhocracy.tests import testtools
from adhocracy.tests.testbrowser import ADHOCRACY_LAYER, ADHOCRACY_LAYER_APP
from adhocracy.tests.testbrowser import app_url, instance_url
from adhocracy.tests.testbrowser import Browser


def find_use_cases():
    here = dirname(__file__)
    paths = glob('{here}/use_cases/*.rst'.format(here=here))
    # we need relative paths for DocFileSuite
    pathes = [path.replace(here, '.') for path in paths]
    return pathes


def make_browser():
    return Browser(wsgi_app=ADHOCRACY_LAYER_APP)


use_cases = find_use_cases()
flags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
globs = {"browser": make_browser(),
         'make_browser': make_browser,
         "app": ADHOCRACY_LAYER_APP,
         'self': ADHOCRACY_LAYER,
         "app_url": app_url,
         "instance_url": instance_url,
         # imports
         'mock': mock,
         'testtools': testtools,
         'model': model,
         }


def test_doctests():
    """
    Executes doctests found in `use_cases` one after the other,
    as py.test supports generator based test cases.

    FIXME: to be replaced by proper py.test doctest discovery.

    FIXME: This currently doesn't work. Tests always pass, even if they're
    broken.
    """

    def perform_doctest(path):
        test = DocFileTest(
            path,
            # add here aditional testfiles
            setUp=ADHOCRACY_LAYER.setUp,
            tearDown=ADHOCRACY_LAYER.tearDown,
            globs=globs,
            optionflags=flags
        )
        result = test.defaultTestResult()
        test.run(result)
        for t in (result.failures + result.errors):
            raise Exception(t[1])

    for path in use_cases:
        yield (perform_doctest, path)
