Viewing reports
===============

.. highlight:: none

Text reports
------------
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


HTML reports
------------
Use the ``-o html`` option to enable much more detailed HTML reports.
These include explanations for every notice,
cross-referenced with the standards,
as well as previews of the actual requests and responses.

Please note that these previews **do not represent exactly**
what was sent on the wire. For example, in an HTTP/1.x request,
a header may have been split into two physical lines,
but will be rendered as one line in the report.

In the top right hand corner of an HTML report,
there’s an *options* menu that allows you to filter the report on the fly:

*Hide boring exchanges*
    Check this to hide all exchanges where no problems were found
    (only debug notices or none at all).

*Boring notices*
    Additional notice IDs or severities that should not be considered problems.
    For example: ``1089 1135 C`` (C for “comment”).
    This will hide all exchanges that have only these notices.

*Hide boring notices*
    Check this if you don’t want to see those boring notices at all.
    They will be hidden even from exchanges that have other problems.

Filtering is independent from :ref:`silencing <silence>`.
You cannot undo silencing with these filtering options.


HTML in text
------------

.. highlight:: console

What if you want full details like in HTML reports, but on a textual display?
Perhaps you’re running HTTPolice on a remote machine via ssh.

You can simply use a text-mode Web browser like `w3m`__::

  $ httpolice -o html ... | w3m -M -T text/html

__ http://w3m.sourceforge.net/
