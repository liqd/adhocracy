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

``Go to (adhocracy)/src/adhocracy/tests and add your test
  (http://pylonsbook.com/en/1.1/testing.html).


Run unit tests
---------------

In an `adhocracy.buildout`_ you have ``bin/py.test``. The default config is
set in .coveragerc and setup.cfg.

  $ bin/test


Add functional doctests tests
---------------------------------

The doctest directory is src/adhocracy/tests/use_cases.
To add the tests start solr and set "run_integrationtests = true" in etc/test.ini.


Run one test file
------------------

::

  $ bin/test -k test_comment


Loadtests with funkload
---------------------------

* loadtests directory: src/adhocracy/tests/loadtests/

* reports directory: var/funkload/reports

* run test bench::

  $ bin/funkload-bench


