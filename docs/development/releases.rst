Release Management
==================

Release Versioning
------------------

For adhocracy we use `semantic versioning <http://semver.org/>`_. This
basically means that a release version consists of a major, a minor and
a patch version (e.g. 1.2.3), where you increment

-  the *major* version when you make incompatible changes,
-  the *minor* version when you add functionality in a
   backwards-compatible manner, and
-  the *patch* version when you make backwards-compatible bug fixes.

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

Limitations
-----------

This setup currently does not contain release stabilization or long
living release branches that receive ongoing support.
