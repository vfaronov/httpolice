General concepts
================

.. highlight:: console

.. _exchanges:

Exchanges
---------
HTTPolice takes HTTP *exchanges* (also known as *transactions*) as input.
Every exchange can consist of 1 request and 1+ responses.
Usually there is just 1 response,
but sometimes there are `interim (1xx) responses`__ before the main one.

__ https://tools.ietf.org/html/rfc7231#section-6.2

If you only want to check the request,
you can omit responses from the exchange.

On the other hand, if you only want to check the *responses*,
you should still provide the request (if possible),
because responses cannot be properly analyzed without it.
If you really have no access to the request, you can omit it,
but **many checks will be disabled**.


Reports
-------
The output of HTTPolice is a *report* containing *notices*.

Every notice has an ID (such as “1061”)
that can be used to :ref:`silence <silence>` it,
and one of three *severities*:

*error*
  Something is clearly wrong.
  For example, a `“MUST” requirement`__ of a standard is clearly violated.

  __ https://tools.ietf.org/html/rfc2119

  Please note that **not all errors may be actual problems**.
  Sometimes there is a good reason to violate a standard.
  Sometimes you just don’t care.
  You decide which errors to fix and which to ignore.
  If you don’t want to see an error, you can :ref:`silence <silence>` it.

*comment*
  Something is *possibly* wrong or sub-optimal, but HTTPolice isn’t sure.
  For example, a `“SHOULD” requirement`__ of a standard is clearly violated.

  __ https://tools.ietf.org/html/rfc2119

*debug*
  This just explains why HTTPolice did (or did not do) something.
  For example, when HTTPolice thinks that a response was served from cache,
  it will report a debug notice to explain why it thinks so.
  This may help you understand further cache-related notices
  for that response.


.. _silence:

Silencing unwanted notices
--------------------------

You can *silence* notices that you don’t want to see.
They will disappear from reports and from the :doc:`api`.

Please note that some notice IDs can stand for a range of problems.
For example, most errors in header syntax are reported as notices 1000 or 1158,
so if you silence them, you may lose a big chunk of HTTPolice’s functionality.

Silencing globally
~~~~~~~~~~~~~~~~~~
When using the ``httpolice`` command-line tool,
you can use the ``-s`` option to specify notice IDs to silence::

  $ httpolice -s 1089 -s 1194 ...

Integration methods have similar mechanisms.
For example, `mitmproxy integration`__ understands the same ``-s`` option.

__ http://mitmproxy-httpolice.readthedocs.io/

Silencing locally
~~~~~~~~~~~~~~~~~
You can also silence notices on individual messages
by adding the special ``HTTPolice-Silence`` header to them.
Its value is a comma-separated list of notice IDs. For example::

  HTTP/1.1 405 Method Not Allowed
  Content-Length: 0
  HTTPolice-Silence: 1089, 1110

Requests can also silence notices on responses (but not vice-versa)
by adding a ``resp`` keyword after an ID::

  GET /index.html HTTP/1.1
  User-Agent: Mozilla/5.0
  HTTPolice-Silence: 1033 resp, 1031
