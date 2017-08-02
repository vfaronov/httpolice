History of changes
==================


0.6.0 - 2017-08-02
~~~~~~~~~~~~~~~~~~

Changed
-------
- Notice `1277`_ (obsolete 'X-' prefix) is now reported only once per message.
- When parsing TCP streams, HTTPolice no longer attempts to process very long
  header lines (currently 16K; they will fail with notice `1006`_/`1009`_)	
  and message bodies (currently 1G; notice `1298`_).
- Notice 1259 (malformed parameter in Alt-Svc) has been removed: the same
  problem is now reported as notice `1158`_.
- The syntax of `chunk extensions`_ is no longer checked.

Added
-----
- Checks for the `Forwarded`_ header (notices `1296`_, `1297`_).

Fixed
-----
- Fixed a few bugs and design problems that caused HTTPolice to use more time
  and memory than necessary in various cases (sometimes much more).
- Fixed some Unicode errors under Python 2.
- Notice `1013`_ is no longer wrongly reported for some headers
  such as Vary.
- Fixed a crash on some pathological values of 'charset' in Content-Type.

.. _Forwarded: https://tools.ietf.org/html/rfc7239
.. _chunk extensions: https://tools.ietf.org/html/rfc7230#section-4.1.1
.. _1009: http://httpolice.readthedocs.io/page/notices.html#1009
.. _1298: http://httpolice.readthedocs.io/page/notices.html#1298
.. _1158: http://httpolice.readthedocs.io/page/notices.html#1158
.. _1296: http://httpolice.readthedocs.io/page/notices.html#1296
.. _1297: http://httpolice.readthedocs.io/page/notices.html#1297
.. _1013: http://httpolice.readthedocs.io/page/notices.html#1013


0.5.2 - 2017-03-24
~~~~~~~~~~~~~~~~~~
- Fixed a few rare crashing bugs found with `american fuzzy lop`_.
- Fixed a couple cosmetic bugs in HTML reports.
- When parsing a message with an unknown `transfer coding`_, HTTPolice now
  correctly skips any checks on its payload body (such as notice `1038`_).

.. _american fuzzy lop: http://lcamtuf.coredump.cx/afl/
.. _transfer coding: https://tools.ietf.org/html/rfc7230#section-4


0.5.1 - 2017-03-15
~~~~~~~~~~~~~~~~~~
- Fixed compatibility with `httpolice-devtool`_ (when you point it to a local
  `hpoliced`_ instance).

.. _httpolice-devtool:
   https://chrome.google.com/webstore/detail/httpolice-devtool/hnlnhebgfcfemjaphgbeokdnfpgbnhgn
.. _hpoliced: https://pypi.python.org/pypi/hpoliced


0.5.0 - 2017-03-12
~~~~~~~~~~~~~~~~~~

Added
-----
- When `analyzing TCP streams`_, HTTPolice now reorders exchanges
  based on the Date header. In other words, messages sent at the same time
  on different connections are now close to each other in the report.
- Checks for the `Prefer`_ mechanism (notices `1285`_ through `1291`_).
- The syntax of method and header names and reason phrases is now checked
  for all messages, not only for those parsed from TCP streams
  (notices `1292`_, `1293`_, `1294`_).
- Check for method names that are not uppercase (notice `1295`_).
- The XML-related features removed in 0.4.0 have been restored.
- Check for cacheable 421 (Misdirected Request) responses (notice `1283`_).
- Check for 202 (Accepted) responses with no body (notice `1284`_).
- HTML reports have been optimized to load slightly faster in browsers.

.. _1283: http://httpolice.readthedocs.io/page/notices.html#1283
.. _1284: http://httpolice.readthedocs.io/page/notices.html#1284
.. _Prefer: https://tools.ietf.org/html/rfc7240
.. _1285: http://httpolice.readthedocs.io/page/notices.html#1285
.. _1291: http://httpolice.readthedocs.io/page/notices.html#1291
.. _1292: http://httpolice.readthedocs.io/page/notices.html#1292
.. _1293: http://httpolice.readthedocs.io/page/notices.html#1293
.. _1294: http://httpolice.readthedocs.io/page/notices.html#1294
.. _1295: http://httpolice.readthedocs.io/page/notices.html#1295
.. _analyzing TCP streams: http://httpolice.readthedocs.io/page/streams.html

Changed
-------
- Titles of many notices were changed to make more sense when viewed alone
  (as in text reports). If you depend on their wording (which you shouldn't),
  you may need to adjust.

Fixed
-----
- Notice `1021`_ is no longer reported on HTTP/2 requests.

.. _1021: http://httpolice.readthedocs.io/page/notices.html#1021

Meanwhile
---------
- `mitmproxy integration`_ has new features for interactive use.

.. _mitmproxy integration:
   http://mitmproxy-httpolice.readthedocs.io/


0.4.0 - 2017-01-14
~~~~~~~~~~~~~~~~~~

Added
-----
- Python 3.6 compatibility.
- Decompression of `brotli`_ compressed payloads (``Content-Encoding: br``).
- Checks for JSON charsets (notices `1280`_ and `1281`_).
- Checks for some wrong media types,
  currently ``plain/text`` and ``text/json`` (notice `1282`_).

.. _brotli: https://tools.ietf.org/html/rfc7932
.. _1280: http://httpolice.readthedocs.io/page/notices.html#1280
.. _1281: http://httpolice.readthedocs.io/page/notices.html#1281
.. _1282: http://httpolice.readthedocs.io/page/notices.html#1282

Removed
-------
- The deprecated constants
  ``httpolice.ERROR``, ``httpolice.COMMENT``, ``httpolice.DEBUG``
  have been removed. Use ``httpolice.Severity`` instead.
- When checking XML payloads, HTTPolice
  no longer takes precautions against denial-of-service attacks,
  because the `defusedxml`_ module does not currently work with Python 3.6.
  DoS attacks against HTTPolice are considered unlikely and non-critical.
- Notice 1275 ("XML with entity declarations") has been removed
  for the same reason.

.. _defusedxml: https://pypi.python.org/pypi/defusedxml/

Other
-----
- There is now a third-party `Chrome extension`_ for HTTPolice.

.. _Chrome extension: https://chrome.google.com/webstore/detail/httpolice-devtool/hnlnhebgfcfemjaphgbeokdnfpgbnhgn


0.3.0 - 2016-08-14
~~~~~~~~~~~~~~~~~~

Added
-----
- HTTPolice now caches more intermediate values in memory,
  which makes it significantly faster in many cases.
- HTTPolice now works correctly under `PyPy`_ (the 2.7 variant),
  which, too, can make it faster on large inputs.
  You will probably need a recent version of PyPy (5.3.1 is OK).
- `HTML reports`_ now have an "options" menu
  to filter exchanges and notices on the fly.
- The ``httpolice`` command-line tool now has
  a ``--fail-on`` option to exit with a non-zero status
  if any notices with a given severity have been reported.
- Work around various problems in HAR files exported by Firefox and `Fiddler`_.
- HTML reports can now display a remark before every request and response
  (enabled with the *Show remarks* checkbox in the "options" menu).
  The ``httpolice`` command-line tool puts the input filename in this remark.
  With the `Python API`_, you can put anything there
  using the ``remark`` argument to ``Request`` and ``Response`` constructors.
- Notices about HTTP/1.x framing errors (such as `1006`_)
  now include the input filename as well.
- Check for missing scheme name in authorization headers (notice `1274`_).
- Check for missing quality values in headers like Accept (notice `1276`_).
- Check for obsolete 'X-' prefix in experimental headers (notice `1277`_).
- Notice `1093`_ recognizes a few more product names as client libraries.

.. _HTML reports: http://httpolice.readthedocs.io/page/reports.html
.. _Fiddler: http://www.telerik.com/fiddler
.. _PyPy: http://pypy.org/
.. _Python API: http://httpolice.readthedocs.io/page/api.html
.. _1006: http://httpolice.readthedocs.io/page/notices.html#1006
.. _1093: http://httpolice.readthedocs.io/page/notices.html#1093
.. _1274: http://httpolice.readthedocs.io/page/notices.html#1274
.. _1276: http://httpolice.readthedocs.io/page/notices.html#1276
.. _1277: http://httpolice.readthedocs.io/page/notices.html#1277

Changed
-------
- For the `tcpick and tcpflow input`_ modes,
  you now have to use different options to tcpick/tcpflow (consult the manual).
- `Text reports`_ no longer show request/response numbers.
  If you parse these reports, you may need to adjust.
- Styles in HTML reports have been tweaked to make them more readable.

.. _Text reports: http://httpolice.readthedocs.io/page/reports.html

Deprecated
----------
- In the `Python API`_,
  the constants ``httpolice.ERROR``, ``httpolice.COMMENT``, ``httpolice.DEBUG``
  have been replaced with a single ``httpolice.Severity`` enumeration,
  and will be removed in the next release.

.. _Python API: http://httpolice.readthedocs.io/page/api.html

Fixed
-----
- The `tcpick and tcpflow input`_ modes should now be more reliable,
  although they still suffer from certain problems.
- CONNECT requests in HAR files are now handled correctly.
- Notices `1053`_ and `1066`_ are no longer reported
  on requests with bodies of length 0.

.. _tcpick and tcpflow input: http://httpolice.readthedocs.io/page/streams.html
.. _1053: http://httpolice.readthedocs.io/page/notices.html#1053
.. _1066: http://httpolice.readthedocs.io/page/notices.html#1066


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

.. _Django integration: http://django-httpolice.readthedocs.io/
.. _silenced: http://httpolice.readthedocs.io/page/concepts.html#silence
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

Fixed
-----
- Input files from tcpick are sorted correctly.
- Notice `1108`_ doesn't crash in non-English locales.
- Notices such as `1038`_ are not reported on responses to HEAD.

.. _1108: http://httpolice.readthedocs.io/page/notices.html#1108
.. _1038: http://httpolice.readthedocs.io/page/notices.html#1038


0.1.0 - 2016-04-25
~~~~~~~~~~~~~~~~~~

- Initial release.
