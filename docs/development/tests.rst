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

``(adhocracy)/src/adhocracy$ adhocpy setup.py compile_catalog``
  Compile the ``.po`` files for all languages to ``.mo`` files.


Run all tests
--------------
 
``(adhocracy)/src/adhocracy/$ ../../bin/nosetests .
  If you do not use the buildout, take care that every dependency is in 
  your pyton path.


Run one test file 
------------------

``(adhocracy)/src/adhocracy/$ ../../bin/nosetest -s adhocracy.tests.test_module
   The -s option enables stdrout, so you can use pdb/ipdb statements in your code.

