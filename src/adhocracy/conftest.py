import os
import sys
import pkg_resources
from paste.deploy import loadapp
import pylons
import pylons.test
from pylons.i18n.translation import _get_translator
import py.test


def pytest_sessionstart():
    # setup resources before any test is executed
    pylonsapp = None
    pylons.test.pylonsapp = pylonsapp
    path = os.getcwd()
    sys.path.insert(0, path)
    pkg_resources.working_set.add_entry(path)
    config_file = py.test.config.inicfg.get("test_ini")
    pylonsapp = pylons.test.pylonsapp = loadapp('config:' + config_file,
                                                relative_to=path)

    # Setup the config and app_globals, only works if we can get
    # to the config object
    conf = getattr(pylonsapp, 'config')
    if conf:
        pylons.config._push_object(conf)

        if 'pylons.app_globals' in conf:
            pylons.app_globals._push_object(conf['pylons.app_globals'])

    # Initialize a translator for tests that utilize i18n
    translator = _get_translator(pylons.config.get('lang'))
    pylons.translator._push_object(translator)
