HTTPolice is a **lint for HTTP requests and responses**.
It checks them for conformance to standards and best practices.

As a command-line tool, it can read `HAR files`__ or raw HTTP/1.x TCP streams.
It can integrate with `mitmproxy`__ for TLS-encrypted and HTTP/2 traffic.
Or you can use it as a Python library (for Python 2.7 and 3.4+).

__ https://en.wikipedia.org/wiki/.har
__ https://mitmproxy.org/

HTTPolice was partly inspired by `REDbot`__, another QA tool for the Web.
But the approach is different: instead of actively testing your server,
HTTPolice just analyzes anything you feed into it.
Thus, it can be used on requests and responses captured
from a real process or test suite.

__ https://redbot.org/

HTTPolice is hosted `on GitHub`__
and released under the MIT license (see ``LICENSE.txt``).

__ https://github.com/vfaronov/httpolice

Problems, suggestions? Feel free to email the author at vfaronov@gmail.com.
