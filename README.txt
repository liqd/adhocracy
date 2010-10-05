
Adhocracy Liquid Democracy Implementation
=========================================

Instances > Categories > Issues > Proposals

Delegation can happen on on all four levels.

Memcache
======================

Adhocracy uses Memcache to cache results such as rendered pages 
and results from time-intensive computations. To use memcache, 
uncomment the memcache config line in your .ini file and point it 
to a running instance of memcache.

If no memcache is configured or available, Adhocracy should still 
function, but displaying proposals that have a lot of votes can take 
a long time. 

Installation and Setup
======================

We recommend that you install ``adhocracy`` inside a virtualenv as it has _many_ dependencies.

You still need to install pylucene by hand sadly (with some tweaks it can also go into the virtualenv).

All dependencies are listed in setup.py so if you want to hack on it, we recommend to install it via::

	python setup.py develop

If you want to just use it, installing ``adhocracy`` via using easy_install (or pip) is recommended::

    easy_install adhocracy

Make a config file as follows::

    paster make-config adhocracy config.ini

Tweak the config file as appropriate and then setup the application::

    paster setup-app config.ini

Then you are ready to go.
