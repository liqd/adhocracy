Internal API Documentation
==========================

Adhocracy does not have a public programming API. There is a plan to develop a 
common *Kernel* interface for *Liquid Democracy* projects. Once such an API 
becomes available, Adhocracy will be modified to implement that API.

Core polling logic
------------------

.. automodule:: adhocracy.lib.democracy.decision
    :members: 
    :undoc-members:


Delegation management and traversal
-----------------------------------

.. automodule:: adhocracy.lib.democracy.delegation_node
    :members: 


Database models and helper classes
----------------------------------



Badge
'''''

.. automodule:: adhocracy.model.badge
		:members: 
		:undoc-members:


Comment
'''''''

.. automodule:: adhocracy.model.comment
		:members: 
		:undoc-members:


Delegateable
''''''''''''

.. automodule:: adhocracy.model.delegateable
		:members:
		:undoc-members:
    


Delegation
''''''''''

.. automodule:: adhocracy.model.delegation
		:members:
		:undoc-members:


Event
'''''

.. automodule:: adhocracy.model.event
		:members: 
		:undoc-members:


Group
'''''

.. automodule:: adhocracy.model.group
		:members: 
		:undoc-members:


Instance
''''''''

.. automodule:: adhocracy.model.instance
		:members: 
		:undoc-members:


Membership
''''''''''

.. automodule:: adhocracy.model.membership
		:members: 
		:undoc-members:



Milestone
'''''''''

.. automodule:: adhocracy.model.milestone
		:members: 
		:undoc-members:


Openid
''''''

.. automodule:: adhocracy.model.openid
		:members: 
		:undoc-members:



Page
''''

.. automodule:: adhocracy.model.page
		:members: 
		:undoc-members:


Permission
''''''''''

.. automodule:: adhocracy.model.permission
		:members: 
		:undoc-members:


Poll
''''

.. automodule:: adhocracy.model.poll
		:members: 
		:undoc-members:

Proposal
''''''''

.. automodule:: adhocracy.model.proposal
		:members: 
		:undoc-members:

Revision
''''''''

.. automodule:: adhocracy.model.revision
		:members: 
		:undoc-members:


Selection
'''''''''

.. automodule:: adhocracy.model.selection
		:members: 
		:undoc-members:


Tag
'''

.. automodule:: adhocracy.model.tag
		:members: 
		:undoc-members:


Tagging
'''''''

.. automodule:: adhocracy.model.tagging
		:members: 
		:undoc-members:


Tally
'''''

.. automodule:: adhocracy.model.tally
		:members:
		:undoc-members:
		
Text
''''

.. automodule:: adhocracy.model.text
		:members: 
		:undoc-members:


Twitter
'''''''

.. automodule:: adhocracy.model.twitter
		:members: 
		:undoc-members:


User
''''

.. automodule:: adhocracy.model.user
		:members: 
		:undoc-members:

Vote
''''

.. automodule:: adhocracy.model.vote
		:members:
		:undoc-members:


Watch
'''''

.. automodule:: adhocracy.model.watch
		:members: 
		:undoc-members:


    
Template Variables
------------------

Pylons provides a thread local variable
:attr:`pylons.tmpl_context` that is available in templates a
`c`. The following variables are commonly or always available in
templates:

`c.instance`
  A :class:`adhocracy.model.Instance` object or `None`. It is set by
  :class:`adhocracy.lib.base.BaseController` from a value determinated
  by :class:`adhocracy.lib.instance.DescriminatorMiddleware` from the
  host name.

`c.user`
  A :class:`adhocracy.model.User` object or `None` if unauthenticated.
  It is set by :class:`adhocracy.lib.base.BaseController` from a value
  determinated by the :mod:`repoze.who` middleware.

`c.active_global_nav`
  A `str` naming the current active top navigation item. It is set to
  'instance' in :class:`adhocracy.lib.base.BaseController` if the
  request is made to an instance and can be overridden in any
  controller.
