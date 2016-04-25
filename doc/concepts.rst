General concepts
================

.. _exchanges:

Exchanges
---------
HTTPolice takes HTTP *exchanges* (also known as *transactions*) as input.
Every exchange can consist of one request and one or more responses.
Usually there is just one response,
but sometimes there are `interim (1xx) responses`__ before the main one.

__ https://tools.ietf.org/html/rfc7231#section-6.2

If you only want to check the request,
you can omit the responses from an exchange.

On the other hand, if you only want to check the *responses*,
you should still provide the request (if at all possible),
because responses cannot be properly analyzed without it.
If you really have no access to the request, you can omit it,
but **many checks will be disabled**.


Reports
-------
The output of HTTPolice is a *report* containing *notices*.

Every notice has an ID (such as “1061”) and one of three *severities*:

*error*
  Something is clearly wrong.
  For example, a `“MUST” requirement`__ of a standard is clearly violated.

  __ http://tools.ietf.org/html/rfc2119

  Please note that **not all errors may be actual problems**.
  Sometimes there is a good reason to violate a standard.
  Sometimes you just don’t care.
  You decide which errors to fix and which to ignore.

*comment*
  Something is *possibly* wrong or sub-optimal, but HTTPolice isn’t sure.
  For example, a `“SHOULD” requirement`__ of a standard is clearly violated.

  __ http://tools.ietf.org/html/rfc2119

*debug*
  This just explains why HTTPolice did (or did not do) something.
  For example, when HTTPolice thinks that a response was served from cache,
  it will report a debug notice to explain why it thinks so.
  This may help you understand further cache-related notices
  for that response.
