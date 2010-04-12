Platform Basics
===============

In order to work with Adhocracy's API, one should first understand 
some of the fundamental metaphors used on the site. 

Overview 
--------

The core process of Adhocracy is focussed around the creation and 
collaborative development of (policy) ``Proposals``. These can include
any normative text, ranging from strategy documents to full-fledged 
legislation drafts. 

The development of ``Proposals`` itself is centered around the 
selection of ``Texts`` for inclusion in the ``Proposal`` language. 
Each such ``Text`` is a variant of a ``Page``, a given document such 
as a law or a statute. 

Throughout this process, voting takes place. ``Polls`` can be used 
to both rate, support or adopt a given proposition. As such, any 
``Poll`` can relate to either ``Texts``, user ``Comments`` or 
entire ``Proposals``. 

Participation in a ``Poll`` can either be direct, or take place via 
a ``Delegation``. Delegated voting will allow an agent (i.e. another
voter) to cast multiple votes within a specified scope. A ``Delegation`` 
can be revoked (i.e. permanently removed) or overridden (i.e. overruled 
with regards to a specific ``Poll``) by the principal (the delegating 
user) at any time.

A special mode of ``Poll`` can be used for proposal adoption. While in 
most ``Polls``, the result is expressed either as absolute numbers of 
voters for or against the subject or as a ``Poll`` score (i.e. net 
support), adoption ``Polls`` aim to make a definitive decision. To 
achieve this, a stability criterion is introduced. This means that a 
``Poll`` to adopt a specific ``Proposal`` is considered successful if 
it has both achieved a quorum of votes and held a specified majority 
(e.g. 66% of votes cast) for a specified interval of time (e.g. one 
week).

Instances 
---------

Adhocracy is a multi-tenant web platform. Any group or organisation 
using the site will create its own ``Instance`` which can be 
configured to best meet the group's wishes. While ``Users`` need 
only sign up once, discussions and drafts are held completely 
isolated among different ``Instances``. Instance configuration options 
include such aspects as user memberships, voting specifics and 
some layout options.  

Any REST request must thus be made addressing a specific instance 
(by using the appropriate subdomain: http://instance_key.site.url).
Exceptions include the listing and creation of ``Instances`` as well as
the listing, creation and manipulation of ``User``. 


Delegation Tree
---------------

One very fundamental structure within Adhocracy is the delegation 
tree. It is used to determine the scope of voting delegations within
the system. Most elements within the platform, such as ``Proposals``, 
``Issues`` and ``Pages`` are a part of this tree by inheriting from 
the ``Delegateable`` class. Each ``Delegateable`` node can have many 
parents and many children. A ``Delegation`` within the scope of a 
``Delegateable`` will thus apply to any voting decisions regarding 
the ``Delegateable`` and any of its children, recursively. 

Since the Delegation tree is very flexible, there is no method of making 
sure that only one ``Delegation`` applies to a specific scope. In cases 
where multiple ``Delegations`` match, less specific ``Delegations`` are 
discarded (i.e. those that apply to a parent of the scope, rather 
than the scope itself). If multiple ``Delegations`` match after such 
disambiguation, reconciliation is attempted at a later stage, during 
vote tallying. Currently, this means that if all delegates voted 
in the same way, the vote is counted; else it will be discarded and 
the user will be informed. 

