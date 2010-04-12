
REST API
========

Adhocracy provides a REST-inspired API for client applications to 
remotely gather or submit data or to synchronize Adhocracy sign-ups
and voting processes with other sites. 

While at the moment only JSON and RSS is produced and only JSON is
processed by the software, future support for other formats, such as 
XML (i.e. StratML, EML) is planned. 


Data Submission
---------------

All data submitted is expected to be either URL-encoded (for GET requests) 
or ``application/x-www-form-urlencoded`` (i.e. formatted as an HTML form). 
Accept/Content-type based submission of JSON/XML data will be implemented 
in a later release.

A meta parameter called ``_method`` is evaluated for each request to fake a 
request method if needed. This is useful for older HTTP libraries or 
JavaScript clients which cannot actually perform any of the more exotic 
HTTP methods, such as PUT and DELETE.


Authentication and Security
---------------------------

Authentication can take place either via form-based cookie creation
(POST ``login`` and ``password`` to ``/perform_login``) or via HTTP
Basic authentication (i.e. via HTTP headers). 

Please note that for any write action using a cookie-based session,
the site will expect an additional request parameter, ``_tok``, containing
a session ID. This is part of Adhocracy's CSRF filter and it will 
not apply to requests made using HTTP Basic authentication.  

OAuth-based authorization is planned for a future release and will 
allow for token-based access to specific resources or operations. 


Pagination
----------

Many listings in Adhocracy are powered by a common pager system. Each
pager has a specific prefix (e.g. ``proposals_``) and a set of request 
parameters that can be used to influence the pager:

* ``[prefix]_page``: The page number to retrieve, i.e. offset.
* ``[prefix]_count``: Number of items to retrieve per page. 
* ``[prefix]_sort``: Sorting key. These are somewhat erratically numbered and need to be redone in the future.
* ``[prefix]_q`` (in some cases): A search query used to filter the items.



Resources 
=========

``/instance`` - Group/Organization Instances
--------------------------------------------


index
*****

* List all existing and non-hidden instances.
* URL: ``http://[instance].adhocracy.cc/instance[.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: no
* Pager prefix: ``instances_``

create
******

* Create a new instance for a group or organization.
* URL: ``http://[instance].adhocracy.cc/instance[.format]``
* Method: ``POST``
* Formats: ``html, json``
* Authentication: yes
* Parameters:
 * ``key``: A unique identifier for the instance. Short lower-case alpha-numeric text. This cannot be edited after the instance creation. 
 * ``label``: A title for the instance. 
 * ``description``: Short description for the instance, e.g. a mission statement.


show
****

* View an instance's home page or base data
* URL: ``http://[instance].adhocracy.cc/instance/[key][.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: no
* *Note*: If no instance subdomain has been specified, this will 302 to the actual instance.


update
******

* Update some of an instance's properties.
* URL: ``http://[instance].adhocracy.cc/instance[.format]``
* Method: ``PUT``
* Formats: ``html, json``
* Authentication: yes
* Parameters: 
 * ``label``: A title for the instance. 
 * ``description``: Short description for the instance, e.g. a mission statement.
 * ``required_majority``: The percentage of voters required for the adoption of a proposal (e.g. 0.66 for 66%).
 * ``activation_delay``: Delay (in days) that a proposal needs to maintain a majority to be adopted. 
 * ``allow_adopt``: Whether to allow adoption polls on proposals (``bool``). 
 * ``allow_delegate``: Whether to enable delegated voting (``bool``).
 * ``allow_index``: Allow search engine indexing (via robots.txt, ``bool``).
 * ``hidden``: Show instance in listings. 
 * ``default_group``: Default group for newly joined members (one of: ``observer``, ``advisor``, ``voter``, ``supervisor``).


delete
******

* Delete an instance and all contained entities. 
* URL: ``http://[instance].adhocracy.cc/instance/[key][.format]``
* Method: ``DELETE``
* Formats: ``html, json``
* Authentication: yes *(requires global admin rights)*
* *Note*: This will also delete all contained items, such as proposals, delegations, polls or comments.


activity
********

* Retrieve a list of the latest events relating to this instance.
* URL: ``http://[instance].adhocracy.cc/instance/[key]/activity[.format]``
* Method: ``GET``
* Formats: ``html, rss``
* Authentication: no
* Pager prefix: ``events_``


join 
****

* Make the authenticated user a member of this ``Instance``.
* URL: ``http://[instance].adhocracy.cc/instance/[key]/join[.format]``
* Method: ``GET``
* Formats: ``html``
* Authentication: yes
* *Note*: Fails if the user is already a member of the instance. 

leave
*****

* Terminate the authenticated user's membership in this ``Instance``.
* URL: ``http://[instance].adhocracy.cc/instance/[key]/leave[.format]``
* Method: ``POST``
* Formats: ``html``
* Authentication: yes
* *Note*: Fails if the user is not a member of the instance. 



``/user`` - User Management 
---------------------------

* votes
* delegations 
* instances
* issues 
* proposals
* groupmod!
* kick!

``/proposal`` - Proposal drafting
---------------------------------

* delegations
* canonicals
* alternatives
* activity
* adopt!
* tag! 
* untag!



``/poll`` - Poll data and voting
--------------------------------

show
****

* View a poll, listing the current decisions and offering a chance to vote.
* URL: ``http://[instance].adhocracy.cc/poll/[id][.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: no

delete
******

* End a poll and close voting.
* URL: ``http://[instance].adhocracy.cc/poll/[id][.format]``
* Method: ``DELETE``
* Formats: ``html, json``
* Authentication: yes
* *Note*: This will only work for adoption polls, rating polls cannot be terminated.

votes
*****

* Retrieve a list of the decisions that were made regarding this poll.
* URL: ``http://[instance].adhocracy.cc/poll/[id]/votes[.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: no
* Pager prefix: ``decisions_``
* Parameters: 
 * ``result``: Filter for a specific decision, i.e. -1 (No), 1 (Yes), 0 (Abstained).

rate 
****

* Vote in the poll via rating.
* URL: ``http://[instance].adhocracy.cc/poll/[id]/rate[.format]``
* Method: ``POST``
* Formats: ``html, json``
* Authentication: yes
* *Note*: This implements relative voting, i.e. if a user has previously voted -1 and now votes 1, the result will be 0 (a relative change). Used for comment up-/downvoting. Unlike ``vote``, this will also trigger an automated tallying of the poll. It is thus slower, especially for large polls. 

vote
*****

* Vote in the poll.
* URL: ``http://[instance].adhocracy.cc/poll/[id]/vote[.format]``
* Method: ``POST``
* Formats: ``html, json``
* Authentication: yes
* *Note*: This does not trigger tallying. Thus a subsequent call to ``show`` might yield an incorrect tally until a server background job has run.



``/comment`` - Commenting and comment history
---------------------------------------------

* history
* revert! 


``/delegation`` - Vote delegation management
--------------------------------------------

index
*****

* List all existing delegations.
* URL: ``http://[instance].adhocracy.cc/delegation[.format]``
* Method: ``GET``
* Formats: ``json, dot``
* Authentication: no
* Pager prefix: ``delegations_``
* *Note*: The ``dot`` format produces a graphviz file. 


create
******

* Create a new delegation to a specified principal in a given scope.
* URL: ``http://[instance].adhocracy.cc/delegation[.format]``
* Method: ``POST``
* Formats: ``html, json``
* Authentication: yes
* Parameters:
 * ``scope``: ID of the ``Delegateable`` which will be the delegation's scope.
 * ``agent``: User name of the delegation recipient.
 * ``replay``: Whether or not to re-play all of the agents previous decisions within the scope.


show
****

* View the delegation. 
* URL: ``http://[instance].adhocracy.cc/delegation/[id][.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: no
* Pager prefix: ``decisions_`` 
* *Note*: For ``json`` this will return a tuple of the actual serialized delegation and a list of decisions. 


delete
******

* Revoke a the delegation. 
* URL: ``http://[instance].adhocracy.cc/delegation/[id][.format]``
* Method: ``DELETE``
* Formats: ``html, json``
* Authentication: yes
* *Note*: Can only be performed by the delegation's principal.


