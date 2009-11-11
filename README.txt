
Adhocracy Liquid Democracy Implementation
=========================================



Memcache
======================

Adhocracy uses Memcache to cache results such as rendered pages 
and results from time-intensive computations. To use memcache, 
uncomment the memcache config line in your .ini file and point it 
to a running instance of memcache.

If no memcache is configured or available, Adhocracy should still 
function, but displaying motions that have a lot of votes can take 
a long time. 

Installation and Setup
======================

Install ``adhocracy`` using easy_install::

    easy_install adhocracy

Make a config file as follows::

    paster make-config adhocracy config.ini

Tweak the config file as appropriate and then setup the application::

    paster setup-app config.ini

Then you are ready to go.
