Adhocracy Liquid Democracy 
===========================
 
Adhocracy is a policy drafting tool for distributed groups.
It allows members of organizations or the public to compose
or vote documents that represent the policy of the group.

In order to allow cooperation, Adhocracy uses LiquidDemocracy,
a set of ideas that include delegating a user's voting rights
to another to enable both active and passive participation in
the process. We also implement ideas from  Direkter Parlamentarismus,
a theory of mass participation in parliamentary processes.

Installation instructions and further information can be found at
http://trac.adhocracy.cc/wiki/InstallationInstructions

This version requires Python 2.5 or later. 


Implementation details
======================

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
function, but displaying proposals that have a lot of votes or comments
can take a long time.

It also uses solr for searches and rabbitmq to schedule asyncron 
tasks. Both are mandatory.


Installing Adhocracy is a somewhat complicated process. To have a reproducable 
and fast way to set up development and production environments we use 
`zc.buildout`_. You can download our buildout configuration
at https://bitbucket.org/liqd/adhocracy.buildout
The README of adhocray.buildout has extensive information about the setup process.

