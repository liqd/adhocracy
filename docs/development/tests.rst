Add and run tests
===================

Before every commit you have to run all tests. Every new feature
has to have a good test coverage. You should use Test Driven Develpment
(http://en.wikipedia.org/wiki/Test-driven_development) and Acceptance Test
Driven Develpment. Acceptance Tests correspondence to user stories
(http://en.wikipedia.org/wiki/User_story). They use TestBrowser
sessions and reside inside the functional tests directory.


Add a new test
--------------

``Go to (adhocracy)/src/adhocracy/adhocracy/tests and add you test
  (http://pylonsbook.com/en/1.1/testing.html).


Run unit tests
---------------

In an `adhocracy.buildout`_ you have ``bin/test``. Alternatively you can call::

  (adhocracy)$ bin/nosetests --with-pylons=etc/test.ini src/adhocracy/adhocracy/tests``


Add functional doctests tests
---------------------------------

The doctest directory is src/adhocracy/adhocracy/test/use_cases.
To add the tests start solr and set "run_integrationtests = true" in src/adhocracy/test.ini.


Run one test file
------------------

::

  (adhocracy)/src/adhocracy/$ ../../bin/nosetest -s adhocracy.tests.test_module

The -s option enables stdout, so you can use pdb/ipdb statements in your code.

.. _adhocracy.buildout: https://bitbucket.org/liqd/adhocracy.buildout
