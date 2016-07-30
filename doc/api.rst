Python API
==========

HTTPolice can be used as a Python library:
for example, to analyze requests or responses as part of a test suite.
It is **not intended** to be used inside live production processes.


Example
-------
.. literalinclude:: api_example.py


API reference
-------------
.. autoclass:: httpolice.Request
   :members: notices, silence

|

.. autoclass:: httpolice.Response
   :members: notices, silence

|

.. autoclass:: httpolice.Exchange
   :members: silence

   .. attribute:: request

      The :class:`~httpolice.Request` object passed to the constructor.

   .. attribute:: responses

      The list of :class:`~httpolice.Response` objects
      passed to the constructor.

|

.. autofunction:: httpolice.check_exchange

|

.. autoclass:: httpolice.Complaint
   :members: id, severity

|

.. autoclass:: httpolice.Severity
   :members:
   :undoc-members:

|

.. autofunction:: httpolice.text_report

|

.. autofunction:: httpolice.html_report


Integration helpers
-------------------
.. automodule:: httpolice.helpers
   :members:
