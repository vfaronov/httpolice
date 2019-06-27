HTTPolice
=========

.. status:
.. image:: https://img.shields.io/pypi/v/HTTPolice.svg
   :target: https://pypi.org/project/HTTPolice/
.. image:: https://img.shields.io/pypi/pyversions/HTTPolice.svg?
   :target: https://pypi.org/project/HTTPolice/
.. image:: https://readthedocs.org/projects/httpolice/badge/?version=stable
   :target: https://httpolice.readthedocs.io/
.. image:: https://travis-ci.org/vfaronov/httpolice.svg?branch=master
   :target: https://travis-ci.org/vfaronov/httpolice

HTTPolice is a **validator or “linter” for HTTP requests and responses**.
It can spot bad header syntax, inappropriate status codes, and other potential
problems in your HTTP server or client.

See `example report`__.

__ https://httpolice.readthedocs.io/page/showcase.html

As a command-line tool, it can read `HAR files`__ or raw HTTP/1.x TCP streams.
It can `integrate with mitmproxy`__ for TLS-encrypted and HTTP/2 traffic.
Or you can use it as a Python (3.4+) library.
There is a `Django integration`__ package and a third-party `Chrome extension`__.

__ https://en.wikipedia.org/wiki/.har
__ https://github.com/vfaronov/mitmproxy-httpolice
__ https://github.com/vfaronov/django-httpolice
__ https://chrome.google.com/webstore/detail/httpolice-devtool/hnlnhebgfcfemjaphgbeokdnfpgbnhgn

Start with the `quickstart`__.

__ https://httpolice.readthedocs.io/page/quickstart.html

A full `user manual`__ is available.
Also, a `list of all problems`__ HTTPolice can detect.

__ https://httpolice.readthedocs.io/
__ https://httpolice.readthedocs.io/page/notices.html

HTTPolice was partly inspired by `REDbot`__, another QA tool for the Web.
But the approach is different: instead of actively testing your server,
HTTPolice just analyzes anything you feed into it.
Thus, it can be used on requests and responses captured
from a real process or test suite.

__ https://redbot.org/

HTTPolice is hosted `on GitHub`__
and released under the MIT license (see ``LICENSE.txt``).
If you want to hack on HTTPolice, check out ``HACKING.rst``.

__ https://github.com/vfaronov/httpolice

`BrowserStack`__ kindly provide a free subscription for testing HTTPolice.

__ https://www.browserstack.com/
