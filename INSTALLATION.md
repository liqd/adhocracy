Adhocracy development buildout
==============================

This buildout sets up an adhocracy development env and all dependencies.
It compiles nearly all dependecies to make a repeatable and isolated
enviroment. It is tested on linux and will probably run on OS X.

It sets up a bunch of servers and configures supervisor to run them:

* adhocracy (http server that runs adhocracy with Spawning/WSGI)
* adhocracy_background (background queue processing)
* solr (searching)
* memcached (code cache)
* rabbitmq (internal messaging queue)
* supervisor


Installation
------------
 
Automatic installation on debian or Ubuntu with build_debian.sh
----------------------------------------------------------------

On debian or Ubuntu, you can simply execute the following in a terminal:

    wget -nv https://raw.github.com/liqd/adhocracy.buildout/master/build_debian.sh -O build_debian.sh && sh build_debian.sh

The script will use sudo to install the required dependencies, and install, set up, and start the required database services.

Add the `-p` option to use PostgreSQL or the `-m` option to use MySQL instead of the default sqlite. Add `-b develop` to install the development version, or `-b hhu` to install with the preconfiguration for HHU Düsseldorf.

Developer instructions
----------------------

adhocracy itself gets installed in `adhocracy_buildout/src/adhocracy`. To use your own [fork](https://help.github.com/articles/fork-a-repo) instead of the regular("upstream") adhocracy, use [`git remote`](http://www.kernel.org/pub/software/scm/git/docs/git-remote.html):

    $ git remote -v
    origin  https://github.com/liqd/adhocracy (fetch)
    origin  https://github.com/liqd/adhocracy (push)
    $ git remote add USERNAME https://github.com/USERNAME/adhocracy
    $ git push USERNAME

You can now execute `git pull origin` to update your local copy with new upstream changes. Use [`commit`](http://www.kernel.org/pub/software/scm/git/docs/git-commit.html) and [`push`](http://www.kernel.org/pub/software/scm/git/docs/git-push.html) to record and publish your changes.  As soon as you are confident that you have implemented a feature or corrected a bug, create a [pull request](https://help.github.com/articles/using-pull-requests) to ask the core developers to incorporate your changes.

Manual installation on other systems
----------------------------------- 

Install needed system packages (Debian example):

   $ sudo apt-get install libpng-dev libjpeg-dev gcc make build-essential bin86 unzip libpcre3-dev zlib1g-dev mercurial git
   $ sudo apt-get install python python-virtualenv  (2.7)
   $ sudo apt-get install libsqlite3-dev postgresql-server-dev-8.4
   $ sudo apt-get install openjdk-6-jre 
   $ sudo apt-get install erlang-dev erlang-mnesia erlang-os-mon xsltproc

To make the apache vhost config work run:

   $ sudo apt-get install libapache2-mod-proxy-html
   $ sudo a2enmod proxy proxy_http proxy_html

Checkout out adhocracy:

   $ git clone https://github.com/liqd/adhocracy adhocracy_buildout  
 
Run buildout:

    $ python bootstrap.py --version=1.7.0 
    $ bin/buildout

Start adhocracy and dependency servers):

    $ bin/supervisord 

If you do not use the buildout to compile and start the postgres database system,
you have to setup the adhocracy database manually:

    $ bin/paster setup-app etc/adhocracy.ini --name=content


Additional steps in adhocracy geo branch
----------------------------------------

Install the libgeos library with all development files.

Make sure `adhocracy.buildout` and `src/adhocracy` are both checked out in geo
branch.

The buildout initializes the local postgres database cluster with PostGIS, 
as described in`src/adhocracy/docs/initialize-postgis.rst'.

In case you want to prefill the `region` table with Openstreetmap data, follow
the docs in `src/adhocracy/docs/imposm-setup.txt`.

Note: The geo currently requires PostgreSQL with PostGIS, MySQL-spatial and
SQLite SpatiaLite will not work. Some work towards building Adhocracy with
SpatiaLite has happened in the spatialite branch of `adhocracy.buildout`.


Run adhocracy
-------------

Start adhocracy and  all dependency servers:
    $ bin/supervisord 

Restart servers:
    $ bin/supervisorctl reload 

View the status of all servers:
    $ bin/supervisorctl status

To start/stop one server:
    $ bin/supervisorctl stop <name>

Start the adhocracy server in foreground mode:
    $ bin/supervisorctl stop adhocracy
    $ bin/paster serve etc/adhocracy.ini


Buildout configuration
----------------------

Read  `buildout_commmon.cfg` and `buildout_development.cfg` to learn all 
buildout configuration options. 
Customize buildout.cfg to change the domains, ports and server versions.
Instead of compiling all dependencies (postgres, solr,..) you can also use system packages.
Just use your custom buildout file to remove the included files you do not need:

    [buildout]
    extends = buildout_development.cfg
    extends -=  
        buildouts/postgres.cfg 
