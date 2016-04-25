Viewing reports
===============

.. highlight:: none

By default, HTTPolice produces simple plain text reports like this::

  ------------ request 1 : PUT /articles/109226/
  E 1000 Malformed If-Match header
  C 1093 User-Agent contains no actual product
  ------------ response 1 : 100 Continue
  ------------ response 2 : 204 No Content
  C 1110 204 response with no Date header
  E 1221 Strict-Transport-Security without TLS
  ------------ request 2 : POST /articles/109226/comments/
  ...

They are intended to be suitable for grep and other Unix-like tools.

Use the ``-o html`` option to enable HTML reports.
These are much more detailed, including:

- previews of the actual requests and responses;
- explanation for every notice;
- cross-references to the standards;

and more.

.. highlight:: console

What if you want full details like in HTML reports, but still in plain text?
Just use a text-mode Web browser like `w3m`__::

  $ httpolice -o html ... | w3m -M -T text/html

__ http://w3m.sourceforge.net/
