Upgrading Adhocracy installations
=================================

In order to upgrade an existing Adhocracy installation you need to perform some
general steps. Further required steps may be described in section of the
respective releases in the CHANGES.txt document.


General steps
-------------

The general upgrading steps are roughly the following:


Stop the running installation::

    bin/supervisorctl shutdown

Upgrade the source code to the desired version, e.g. in order to upgrade to
version 2.4.0, do::

    git fetch
    git checkout 2.4.0

If needed, adopt your configuration::

    vi buildout-my.cfg

Run buildout::

    bin/buildout -c buildout-my.cfg

Start supervisor again::

    bin/supervisord

Perform database migrations, create new permissions::

    bin/paster setup-app etc/adhocracy.ini --name=content


Additional steps / Caveats
--------------------------

In addition to the general steps, it is sometimes required to perform some
additional upgrade tasks. If this is needed, this should be documented in
CHANGES.txt.

Reindex Solr
~~~~~~~~~~~~

Reindex the Solr database::

    bin/paster index -c etc/adhocracy.ini

Alternatively, if you think Solr contains some objects which should be deleted,
you may want to drop the Solr database entirely and rebuild it from scratch::

    bin/paster index DROP -c etc/adhocracy.ini
    bin/paster index -c etc/adhocracy.ini

Rebuild python
~~~~~~~~~~~~~~

If the version of the included python has been changed, you may want to rebuild
python:

    git submodule update
    cd python
    python bootstrap.py
    bin/buildout
    cd ..

And rerun bootstrap (see below).

Rebootstrap buildout
~~~~~~~~~~~~~~~~~~~~

If the buildout version is changed, you may want to rebootstrap the buildout
script prior to running buildout:

    bin/python bootstrap.py
    bin/buildout -c buildout-my.cfg
