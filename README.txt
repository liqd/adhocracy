
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

Please consult INSTALL.txt
