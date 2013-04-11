Maintain adhocracy dependencies
===========================


Python dependencies
~~~~~~~~~~~~~~~~~~~

setup.py
---------

Direct dependencies are manually tracked in setup.py. This should only include minimal versions
if we know that we depend on a certain feature which was included in that version.


versions.cfg
------------

A known-good set of all direct and indirect dependency versions is maintained in versions.cfg.
This makes sure that deployments always receive versions of dependencies which have been tested as good, and avoids breakage through new versions in PyPI.

To update all eggs to the latest release:

* delete all versions in versions.cfg

* rerun buildout in newest mode and catch the picked versions ::

    bin/buildout -n > output

* copy the versions from output to versions.cfg


To update only minor releases:

* run checkversion script and catch the picked versions ::

    bin/checkversions -l 2 > output

* read output and manually update the versions in versions.cfg
