Release Management
==================

Release Versioning
------------------

For adhocracy we want to use `semantic versioning <http://semver.org/>`_. This
basically means that a release version consists of a major, a minor and a patch
version (e.g. 1.2.3), where you increment

-  the *major* version when you make incompatible changes,
-  the *minor* version when you add functionality in a
   backwards-compatible manner, and
-  the *patch* version when you make backwards-compatible bug fixes.

However, version 3 is a complete rewrite already in development. So for
version 2 we cannot increment the major version number. Instead, we increment
the minor version number also for incompatible changes.

Changelog
---------

All changes must be documented in CHANGES.txt. "One change" does typically
translate to "one pull request".  In that case, the author of the pull request
is responsible for the changelog entry.

Branches
--------

There are two main branches:

develop
    next release development

master
    current production release; develop is merged in and a tag is
    created at every minor release

Additionally, there are feature branches (prefixed with ``feature-``)
for developing new features. If you want to add a feature or fix a bug,
first implement it and then create a pull request.

It is mandatory that each pull request is reviewed by a person with
commit access before it is merged. Please rebase your feature branch
against develop and clean up your commit history before creating the
pull request. This makes reviewing much easier.

Small changes like typo or pep8 fixes may be committed directly to
develop.

How to release adhocracy
------------------------

If the steps described above are followed, releasing a new version of adhocracy
is simple. Just run the following commands from adhocracy root folder::

    git checkout master
    git merge develop
    git tag $VERSION
    bin/mkrelease -TCd pypi
    git push --tags

To create a local develop release, just run::

    bin/mkrelease -CTqed localhost:/home/...

Note that you need to have your `.pypirc
http://docs.python.org/2/distutils/packageindex.html#the-pypirc-file`
configured.

Limitations
-----------

This setup currently does not contain release stabilization or long
living release branches that receive ongoing support.
