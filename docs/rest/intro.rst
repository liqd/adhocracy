.. WARNING::
  This is the documentation for the REST interface. Unfortunately 
  it is outdated and parts of the interface may not work anymore.


REST API Conventions
====================

Adhocracy provides a REST-inspired API for client applications to 
remotely gather or submit data or to synchronize Adhocracy sign-ups
and voting processes with other sites. 

While at the moment only JSON and RSS is produced and only JSON is
processed by the software, future support for other formats, such as 
XML (i.e. StratML, EML) is planned. 


Data Submission
---------------

All data submitted is expected to be either URL-encoded (for GET requests) 
or ``application/x-www-form-urlencoded`` (i.e. formatted as an HTML form, for
either POST and PUT requests). Accept/Content-type based submission of 
JSON/XML data will be implemented in a later release.

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
not apply to requests made using HTTP Basic authentication. Since the value
of ``_tok`` is not returned by the API, it is recommended to use HTTP Basic 
for any API applications. 

OAuth-based authorization is planned for a future release and will 
allow for token-based access to specific resources or operations. 


Pagination
----------

Many listings in Adhocracy are powered by a common pager system. Each
pager has a specific prefix (e.g. ``proposals_``) and a set of request 
parameters that can be used to influence the pager:

* ``[prefix]_page``: The page number to retrieve, i.e. page offset.
* ``[prefix]_count``: Number of items to retrieve per page. 
* ``[prefix]_sort``: Sorting key. These are somewhat erratically numbered and need to be redone in the future.
* ``[prefix]_q`` (in some cases): A search query used to filter the items.

