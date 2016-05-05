mitmproxy integration
=====================

.. highlight:: console

`mitmproxy`__ is an advanced HTTP debugging tool.
It can intercept TLS-encrypted connections
by generating certificates on the fly.
It supports HTTP/2, it can work as a reverse proxy...
Cool stuff.

__ https://mitmproxy.org/

HTTPolice comes with an `inline script`__ for mitmproxy
that will check intercepted exchanges
and produce a normal HTTPolice :doc:`report <reports>`.
It also works with mitmproxy’s command-line tool `mitmdump`__.

__ http://docs.mitmproxy.org/en/latest/scripting/inlinescripts.html
__ http://docs.mitmproxy.org/en/latest/mitmdump.html

See `mitmproxy docs`__ for instructions on how to install it.
Ubuntu 16.04 “Xenial Xerus” has a `package for mitmproxy 0.15`__
that should be recent enough for HTTPolice.

__ http://docs.mitmproxy.org/en/latest/install.html
__ http://packages.ubuntu.com/xenial/mitmproxy

You will also need to install the integration package (see :doc:`install`)::

  $ pip install mitmproxy-HTTPolice


Usage
-----
To run HTTPolice together with mitmproxy, use a command like this::

  $ mitmdump -s "`python -m mitmproxy_httpolice` -o html report.html"

Note the backticks.
Also, you can replace ``mitmdump`` with ``mitmproxy`` if you wish.

``-s`` is mitmproxy’s option that specifies an inline script to run,
along with arguments to that script.

``python -m mitmproxy_httpolice`` is a sub-command
that prints the path to the script file::

  $ python -m mitmproxy_httpolice
  /home/vasiliy/.local/lib/python2.7/site-packages/mitmproxy_httpolice.py

``-o html`` tells HTTPolice to produce :doc:`HTML reports <reports>`
(omit it if you want a plain text report).
Finally, ``report.html`` is the name of the output file.

Now, mitmproxy/mitmdump starts up as usual.
Every exchange that it intercepts is checked by HTTPolice.
When you stop mitmdump (Ctrl+C) or exit mitmproxy,
HTTPolice writes an HTML report to ``report.html``.

You can use the ``-s`` option to :ref:`silence <silence>` unwanted notices,
just as with the ``httpolice`` command-line tool::

  $ mitmdump -s "`python -m mitmproxy_httpolice` -s 1089 -s 1194 report.txt"
