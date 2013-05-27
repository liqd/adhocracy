Adhocracy installation
======================

Adhocracy makes heavy use of
`buildout <https://pypi.python.org/pypi/zc.buildout>`_, a Python build
tool. It downloads, configures and builds nearly all dependencies to
create a repeatable and isolated environment. In addition it sets up the
supervisord service manager, which allows to easily start and stop the
services which Adhocracy needs to run:

-  adhocracy (http server that runs Adhocracy with Spawning/WSGI)
-  adhocracy\_background (background queue processing)
-  solr (searching)
-  memcached (key-value cache)
-  rabbitmq (internal messaging queue)

Adhocracy is known to work on all modern Linux distributions, but should
also run on OS X and FreeBSD with minor modifications.

There are two supported ways of installing Adhocracy:

-  A fully automatic installation, which downloads and sets up
   everything, is available for Debian, Ubuntu and Arch Linux. This is
   basically a wrapper around buildout.

-  The manual installation, which directly uses the buildout commands.

Both are described in the following.

Automatic installation on debian, Ubuntu or Arch Linux with build.sh
--------------------------------------------------------------------

On debian, Ubuntu, or Arch you can simply execute the following in a
terminal:

::

    wget -nv https://raw.github.com/liqd/adhocracy/develop/build.sh -O build.sh && sh build.sh

The script will use sudo to install the required dependencies, and
install, set up, and start the required services.

Add ``-c hhu`` to install with the preconfiguration for HHU Düsseldorf.

Manual installation
-------------------

## Preparations

Install required system packages (Debian Squeeze example):

::

    $ sudo apt-get install gcc make build-essential bin86 unzip libpcre3-dev mercurial git libssl-dev libbz2-dev
    $ sudo apt-get install python python-setuptools
    $ sudo apt-get install libsqlite3-dev postgresql-server-dev-8.4
    $ sudo apt-get install openjdk-6-jre

To make the apache vhost config work run:

::

    $ sudo apt-get install libapache2-mod-proxy-html
    $ sudo a2enmod proxy proxy_http proxy_html

Check out Adhocracy:

::

    $ git clone https://github.com/liqd/adhocracy
    $ cd adhocracy
    
    $ git submodule init
    $ git submodule update

## Setup an isolated python environment to run Adhocracy

To install Adhocracy you need python (2.6|2.7) with PIL (python imaging) but 
no other system-packages.

Compile python and PIL with the included python buildout::

    $ cd python
    $ python bootstrap.py
    $ bin/buildout
    $ cd ..

## Install and start Adhocracy

Run buildout:

::

    $ bin/python bootstrap.py 
    $ bin/buildout

Start Adhocracy and dependent servers:

::

    $ bin/supervisord

If you do not use the buildout to compile and start the database system
(currently only possible for PostgreSQL, but disabled by default), you
have to setup the Adhocracy database manually:

::

    $ bin/paster setup-app etc/adhocracy.ini --name=content

Run Adhocracy
-------------

Start Adhocracy and all dependent servers:

::

    $ bin/supervisord

Restart servers:

::

    $ bin/supervisorctl reload

View the status of all servers:

::

    $ bin/supervisorctl status

To start/stop one server:

::

    $ bin/supervisorctl stop <name>

Start the Adhocracy server in foreground mode:

::

    $ bin/supervisorctl stop adhocracy
    $ bin/paster serve etc/adhocracy.ini

Buildout configuration
----------------------

-  Read ``buildout_commmon.cfg`` and ``buildout_development.cfg`` to
   learn all buildout configuration options.
-  Customize ``buildout.cfg`` to change the domains, ports and server
   versions.
-  Instead of compiling all dependencies (postgres, solr,..) you can
   also use system packages.
-  Use your custom buildout file to remove the included files you do not
   need:

   [buildout] extends = buildout\_development.cfg parts -= postgresql

Developer instructions
----------------------

To use your own `fork <https://help.github.com/articles/fork-a-repo>`_
instead of the regular("upstream") adhocracy, use
```git remote`` <http://www.kernel.org/pub/software/scm/git/docs/git-remote.html>`_:

::

    $ git remote -v
    origin  https://github.com/liqd/adhocracy (fetch)
    origin  https://github.com/liqd/adhocracy (push)
    $ git remote add USERNAME https://github.com/USERNAME/adhocracy
    $ git push USERNAME

You can now execute ``git pull origin`` to update your local copy with
new upstream changes. Use
```commit`` <http://www.kernel.org/pub/software/scm/git/docs/git-commit.html>`_
and
```push`` <http://www.kernel.org/pub/software/scm/git/docs/git-push.html>`_
to record and publish your changes. As soon as you are confident that
you have implemented a feature or corrected a bug, create a `pull
request <https://help.github.com/articles/using-pull-requests>`_ to ask
the core developers to incorporate your changes.
