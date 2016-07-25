HTTPolice is a **lint for HTTP requests and responses**.
It checks them for conformance to standards and best practices.

See `example report`__.

__ http://pythonhosted.org/HTTPolice/showcase.html

As a command-line tool, it can read `HAR files`__ or raw HTTP/1.x TCP streams.
It can integrate with `mitmproxy`__ for TLS-encrypted and HTTP/2 traffic.
Or you can use it as a Python library (for Python 2.7 and 3.4+),
with optional `Django`__ integration.

__ https://en.wikipedia.org/wiki/.har
__ https://mitmproxy.org/
__ https://www.djangoproject.com/

Start with the `quickstart`__.

__ http://httpolice.readthedocs.io/en/stable/quickstart.html

A full `user manual`__ is available.
Also, a `list of all problems`__ HTTPolice can detect.

__ http://httpolice.readthedocs.io/en/stable/
__ http://pythonhosted.org/HTTPolice/notices.html

HTTPolice was partly inspired by `REDbot`__, another QA tool for the Web.
But the approach is different: instead of actively testing your server,
HTTPolice just analyzes anything you feed into it.
Thus, it can be used on requests and responses captured
from a real process or test suite.

__ https://redbot.org/

HTTPolice is hosted `on GitHub`__
and released under the MIT license (see ``LICENSE.txt``).

__ https://github.com/vfaronov/httpolice

`BrowserStack`__ kindly provide a free subscription for testing HTTPolice.

__ https://www.browserstack.com/

Problems, suggestions? Feel free to email the author at vfaronov@gmail.com.
