
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

Page
''''

.. automodule:: adhocracy.model.page
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

Selection
'''''''''

.. automodule:: adhocracy.model.selection
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

Vote
''''

.. automodule:: adhocracy.model.vote
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

    
Template Variables
------------------

Pylons provides a thread local variable
:attribute:`pylons.tmpl_context` that is available in templates a
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
  determinated by the :module:`repoze.who` middleware.

`c.active_global_nav`
  A `str` naming the current active top navigation item. It is set to
  'instance' in :class:`adhocracy.lib.base.BaseController` if the
  request is made to an instance and can be overridden in any
  controller.
