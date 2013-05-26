.. Adhocracy webservice documentation master file, created by
   sphinx-quickstart on Wed Apr 10 22:31:24 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Adhocracy webservice's documentation!
================================================

Contents:

.. toctree::
   :maxdepth: 2

.. services::
   :modules: adhocracy_kotti.mediacenter

Example usage
-------------

.. literalinclude:: functional_mediacenter.rst


Errors
------

Return erro codes:

* 400 (validation, processing error),
* 500(service not available)

Return value is a JSON dictionary with:

* location is the location of the error. It can be “querystring”, “header” or “body”
* name is the eventual name of the value that caused problems
* description is a description of the problem encountered.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

