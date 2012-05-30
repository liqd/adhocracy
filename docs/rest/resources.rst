.. WARNING::
  This is the documentation for the REST interface. Unfortunately 
  it is outdated and parts of the interface may not work anymore.


REST Resources 
==============

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
* URL: ``http://[instance].adhocracy.cc/instance/[key][.format]``
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


index
*****

* List all users with an active membership in the specified instance.
* URL: ``http://[instance].adhocracy.cc/user[.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: no
* Pager prefix: ``users_``
* Parameters:

  * ``users_q``: A search query to filter with. 
  * ``users_filter``: Filter by membership group (only in an instance context).

* *Note*: If no instance is specified, all registered users will be returned. 


create
******

* Create a new user.
* URL: ``http://[instance].adhocracy.cc/user[.format]``
* Method: ``POST``
* Formats: ``html, json``
* Authentication: no
* Parameters:

  * ``user_name``: A unique user name for the new user. 
  * ``email``: An email, must be validated.
  * ``password``: A password, min. 3 characters. 
  * ``password_confirm``: Must be identical to ``password``.

* *Note*: Does not require an instance to be specified. If an instance is selected, the user will also become a member of that instance.  


show
****

* View an user's home page and activity stream,
* URL: ``http://[instance].adhocracy.cc/user/[user_name][.format]``
* Method: ``GET``
* Formats: ``html, json, rss``
* Authentication: no
* *Note*: Also available outside of instance contexts. 


update
******

* Update the user's profile and settings.
* URL: ``http://[instance].adhocracy.cc/user/[user_name][.format]``
* Method: ``PUT``
* Formats: ``html, json``
* Authentication: yes *(either to own user or with user management permissions)*
* Parameters: 

  * ``display_name``: Display name, i.e. the real name to be shown in the application.
  * ``email``: E-Mail address. Must be re-validated when changed. 
  * ``locale``: A locale, currently: ``de_DE``, ``en_US`` or ``fr_FR``. 
  * ``password``: A password, min. 3 characters. 
  * ``password_confirm``: Must be identical to ``password``.
  * ``bio``: A short bio, markdown-formatted.
  * ``email_priority``: Minimum priority level for E-Mail notifications to be sent (0-6).
  * ``twitter_priority``: Minimum priority level for Twitter direct message notifications to be sent (0-6).


delete
******

* Delete an user. **Not implemented**


votes 
*****

* Retrieve a list of the decisions that were made by this user.
* URL: ``http://[instance].adhocracy.cc/user/[user_name]/votes[.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: no
* Pager prefix: ``decisions_``
* *Note*: Does not include rating polls, limited to adoption polls.


delegations 
***********

* Retrieve a list of the delegations that were created by this user.
* URL: ``http://[instance].adhocracy.cc/user/[user_name]/delegations[.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: no
* Pager prefix: ``delegations_`` *(``json`` view only)*
* *Note*: In ``html``, lists both incoming and outgoing delegations. When rendered as ``json``, this only includes outgoing delegations. 


instances
*********

* A list of all non-hidden instances in which the user is a member. 
* URL: ``http://[instance].adhocracy.cc/user/[user_name]/instances[.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: no
* Pager prefix: ``instances_``


proposals
*********

* A list of all proposals that the user has introduced. 
* URL: ``http://[instance].adhocracy.cc/user/[user_name]/proposals[.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: no
* Pager prefix: ``proposals_``


groupmod
********

* Modify a user's membership in the current instance
* URL: ``http://[instance].adhocracy.cc/user/[user_name]/proposals[.format]``
* Method: ``GET``
* Formats: ``html``
* Authentication: yes *(requires instance admin privileges)*
* Parameters: 

  * ``to_group``: Target group (one of: ``observer``, ``advisor``, ``voter``, ``supervisor``). 


kick
****

* Terminate a user's membership in the current instance
* URL: ``http://[instance].adhocracy.cc/user/[user_name]/proposals[.format]``
* Method: ``GET``
* Formats: ``html``
* Authentication: yes *(requires instance admin privileges)*
* *Note*: Since the user can re-join at any time, this is largely a symbolic action.




``/proposal`` - Proposal drafting
---------------------------------

index
*****

* List all existing proposals in the given instance.
* URL: ``http://[instance].adhocracy.cc/proposal[.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: no
* Pager prefix: ``proposals_``
* Parameters:

  * ``proposals_q``: A search query to filter with. 
  * ``proposals_state``: Filter by state (one of: ``draft``, ``polling``, ``adopted``). Only available if adoption polling is enabled in the selected instance.


create
******

* Create a new proposal.
* URL: ``http://[instance].adhocracy.cc/proposal[.format]``
* Method: ``POST``
* Formats: ``html, json``
* Authentication: yes
* Parameters:

  * ``label``: A title for the proposal. 
  * ``text``: Goals of the proposal.
  * ``tags``: Comma-separated or space-separated tag list to be applied to the proposal.
  * ``alternative`` (multiple values): IDs of any proposals that should be marked as an alternative to this proposal.


show
****

* View an proposals's goal page
* URL: ``http://[instance].adhocracy.cc/proposal/[id][.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: no


update
******

* Update some of a proposal's properties.
* URL: ``http://[instance].adhocracy.cc/proposal/[id][.format]``
* Method: ``PUT``
* Formats: ``html, json``
* Authentication: yes
* Parameters: 
* ``label``: A title for the proposal. 
* ``alternative`` (multiple values): IDs of any proposals that should be marked as an alternative to this proposal.
* *Note*: The goal description and tag list are edited separately. 


delete
******

* Delete a proposal and any contained entities. 
* URL: ``http://[instance].adhocracy.cc/proposal/[id][.format]``
* Method: ``DELETE``
* Formats: ``html, json``
* Authentication: yes *(requires instance admin rights)*
* *Note*: This will also delete all contained items, such as comments and delegations.


delegations 
***********

* Retrieve a list of the delegations that exist regarding this proposal.
* URL: ``http://[instance].adhocracy.cc/proposal/[id]/delegations[.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: no
* Pager prefix: ``delegations_``


canonicals 
**********

* Retrieve a list of canonical comments regarding the proposal. Canonical comments are listed as "provisions" in the UI. 
* URL: ``http://[instance].adhocracy.cc/proposal/[id]/delegations[.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: no
* *Note*: No pager.


alternatives 
************

* Retrieve a list of the alternatives that exist regarding this proposal.
* URL: ``http://[instance].adhocracy.cc/proposal/[id]/alternatives[.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: no
* Pager prefix: ``proposals_``


activity 
********

* Retrieve a list of events within the scope of the given proposal.
* URL: ``http://[instance].adhocracy.cc/proposal/[id]/activity[.format]``
* Method: ``GET``
* Formats: ``html, rss``
* Authentication: no
* Pager prefix: ``events_``


adopt 
*****

* Trigger an adoption poll regarding this proposal. 
* URL: ``http://[instance].adhocracy.cc/proposal/[id]/adopt[.format]``
* Method: ``POST``
* Formats: ``html``
* Authentication: yes
* *Note*: Requires at least one canonical comment. Adoption polls must be enabled on the instance level.


tag 
***

* Apply an additional tag to a proposal (or support an existing tag).
* URL: ``http://[instance].adhocracy.cc/proposal/[id]/tag[.format]``
* Method: ``GET``
* Formats: ``html``
* Authentication: yes
* Parameters:

  * ``text``: Comma-separated or space-separated tag list to be applied to the proposal.


untag 
*****

* Remove a tag association (tagging) from a proposal.
* URL: ``http://[instance].adhocracy.cc/proposal/[id]/untag[.format]``
* Method: ``GET``
* Formats: ``html``
* Authentication: yes
* Parameters:

  * ``tagging``: ID of the tagging association to be removed.

* *Note*: Only taggings created by the user can be removed.




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


index
*****

* List all existing comments.
* URL: ``http://[instance].adhocracy.cc/comment[.format]``
* Method: ``GET``
* Formats: ``json``
* Authentication: no
* Pager prefix: ``comments_``


create
******

* Create a new comment within a specified context.
* URL: ``http://[instance].adhocracy.cc/comment[.format]``
* Method: ``POST``
* Formats: ``html, json``
* Authentication: yes
* Parameters:

  * ``topic``: ID of the Delegateable to which this comment is associated.
  * ``reply``: A parent comment ID, if applicable.
  * ``canonical`` (bool): Specify whether this is part of the implementation description of the proposal to which it will be associated.
  * ``text``: The comment text, markdown-formatted.
  * ``sentiment``: General tendency of the comment, i.e. -1 for negative, 0 for neutral and 1 for a supporting argument.


show
****

* View a comment separated out of their context.
* URL: ``http://[instance].adhocracy.cc/comment/[id][.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: no


update
******

* Create a new revision of the given comment.
* URL: ``http://[instance].adhocracy.cc/comment/[id][.format]``
* Method: ``PUT``
* Formats: ``html, json``
* Authentication: yes
* Parameters:

  * ``text``: The comment text, markdown-formatted.
  * ``sentiment``: General tendency of the comment, i.e. -1 for negative, 0 for neutral and 1 for a supporting argument.


delete
******

* Delete a comment. 
* URL: ``http://[instance].adhocracy.cc/comment/[id][.format]``
* Method: ``DELETE``
* Formats: ``html, json``
* Authentication: yes 
* *Note*: Comments can only be deleted by non-admins if they have not yet been edited.


history
*******

* List all revisions of the specified comment.
* URL: ``http://[instance].adhocracy.cc/comment/[id]/history[.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: yes 
* Pager prefix: ``revisions_``


revert
******

* Revert to an earlier revision of the specified comment. 
* URL: ``http://[instance].adhocracy.cc/comment/[id]/revert[.format]``
* Method: ``GET``
* Formats: ``html, json``
* Authentication: yes
* Parameters:

  * ``to``: Revision ID to revert to.

* *Note*: This will actually create a new revision containing the specified revision's text.




``/delegation`` - Vote delegation management
--------------------------------------------

index
*****

* List all existing delegations (instance-wide).
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


