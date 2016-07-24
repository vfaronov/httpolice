Changelog
=========

All notable changes to HTTPolice will be documented in this file.

This project adheres to `Semantic Versioning <http://semver.org/>`_
(which means it is unstable until 1.0).


Unreleased
~~~~~~~~~~

Added
-----
- `HTML reports`_ now have an "options" menu
  to filter exchanges and notices on the fly.
- The ``httpolice`` command-line tool now has
  a ``--fail-on`` option to exit with a non-zero status
  if any notices with a given severity have been reported.
- Check for missing scheme name in authorization headers (notice `1274`_).
- Check for missing quality values in headers like Accept (notice `1276`_).
- Check for obsolete 'X-' prefix in experimental headers (notice `1277`_).
- Work around more problems in HAR files exported by Firefox.
- Notice `1093`_ recognizes a few more product names as client libraries.

.. _HTML reports: http://pythonhosted.org/HTTPolice/reports.html
.. _1093: http://pythonhosted.org/HTTPolice/notices.html#1093
.. _1274: http://pythonhosted.org/HTTPolice/notices.html#1274
.. _1276: http://pythonhosted.org/HTTPolice/notices.html#1276
.. _1277: http://pythonhosted.org/HTTPolice/notices.html#1277

Changed
-------
- In the `Python API`_,
  the constants ``httpolice.ERROR``, ``httpolice.COMMENT``, ``httpolice.DEBUG``
  have been replaced with a single ``httpolice.Severity`` enumeration
  and will be removed in the next release.

.. _Python API: http://httpolice.readthedocs.io/en/stable/api.html

Deprecated
----------

Removed
-------

Fixed
-----

Security
--------


0.2.0 - 2016-05-08
~~~~~~~~~~~~~~~~~~

Added
-----
- `Django integration`_ (as a separate distribution).
- Unwanted notices can now be `silenced`_.
- Checks for OAuth `bearer tokens`_.
- Checks for the `Content-Disposition`_ header.
- Checks for `RFC 5987`_ encoded values.
- Checks for `alternative services`_.
- Checks for HTTP/1.1 connection control features `prohibited in HTTP/2`_.
- `Stale controls`_ are now recognized.
- Checks for status code `451 (Unavailable For Legal Reasons)`_.

.. _Django integration: http://pythonhosted.org/HTTPolice/django.html
.. _silenced: http://pythonhosted.org/HTTPolice/concepts.html#silence
.. _bearer tokens: http://tools.ietf.org/html/rfc6750
.. _Content-Disposition: http://tools.ietf.org/html/rfc6266
.. _RFC 5987: https://tools.ietf.org/html/rfc5987
.. _alternative services: https://tools.ietf.org/html/rfc7838
.. _prohibited in HTTP/2: https://tools.ietf.org/html/rfc7540#section-8.1.2.2
.. _Stale controls: https://tools.ietf.org/html/rfc5861
.. _451 (Unavailable For Legal Reasons): https://tools.ietf.org/html/rfc7725

Changed
-------
- `mitmproxy integration`_ has been moved into a separate distribution.

.. _mitmproxy integration: http://pythonhosted.org/HTTPolice/mitmproxy.html

Fixed
-----
- Input files from tcpick are sorted correctly.
- Notice `1108`_ doesn't crash in non-English locales.
- Notices such as `1038`_ are not reported on responses to HEAD.

.. _1108: http://pythonhosted.org/HTTPolice/notices.html#1108
.. _1038: http://pythonhosted.org/HTTPolice/notices.html#1038


0.1.0 - 2016-04-25
~~~~~~~~~~~~~~~~~~

Added
-----
- Initial release.
