
Adhocracy Liquid Democracy Implementation
=========================================

Proposals -> Norms -> Comments

Delegation can happen for Proposals and Norms. Norms can be organized
in a tree structure where Delegations and can inherit Delegations from 
parent pages or Proposals that propose changes to a Norm. Comment voting 
take the Delegations of the commented item into account.

Infrastructure and installation
===============================

Adhocracy uses Memcache to cache results such as rendered pages 
and results from time-intensive computations. To use memcache, 
uncomment the memcache config line in your .ini file and point it 
to a running instance of memcache.

If no memcache is configured or available, Adhocracy should still 
function, but displaying proposals that have a lot of votes can take 
a long time. 

It also uses solr for searches and rabbitmq to schedule asyncron 
tasks. Both are mandatory.

Please consult INSTALL.txt for details.
