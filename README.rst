=======
xmodels
=======

.. image:: https://secure.travis-ci.org/berndca/xmodels.png?branch=master
  :target: https://secure.travis-ci.org/berndca/xmodels
  :alt: Build Status

.. image:: https://coveralls.io/repos/berndca/xmodels/badge.png
  :target: https://coveralls.io/r/berndca/xmodels
  :alt: Coverage

**For more information, please see our documentation:** http://xmodels.readthedocs.org/en/latest/


Overview
========

xmodels is a Python library to convert XML documents and Python dictionaries
including collections.OrderedDict to and from instances of Python data
structures and validate them against a schema.
The conversions between XML and Python dict/collections.OrderedDict are
performed by `xmltodict <https://pypi.python.org/pypi/xmltodict>`_.
It supports XML specific schema features like ordered sets of element type
**<xsd:sequence>**, selection from a set of element type
**<xsd:choice>** and namespaces.
