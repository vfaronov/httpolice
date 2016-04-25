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

If you have multiple Python environments (like `virtualenv`__),
HTTPolice must be installed into **the same environment** as mitmproxy.
Also note that mitmproxy only supports Python 2 (currently).

__ https://virtualenv.pypa.io/en/latest/


Usage
-----
To run HTTPolice together with mitmproxy, use a command like this::

  $ mitmdump -s "`python -m httpolice.plus.mitmproxy` -o html report.html"

(or ``mitmproxy`` instead of ``mitmdump``)

There’s a lot going on there. Let’s take a closer look.

``-s`` is mitmproxy’s option that specifies an inline script to run,
along with arguments *to that script*.

``python -m httpolice.plus.mitmproxy`` is a sub-command
that prints the path to the script file (installed with HTTPolice)::

  $ python -m httpolice.plus.mitmproxy
  /home/vasiliy/.local/lib/python2.7/site-packages/httpolice/plus/mitmproxy.py

This sub-command is wrapped in backticks
to insert its output back into the mitmproxy command.
Thus, mitmproxy’s ``-s`` option gets an argument like this::

  .../httpolice/plus/mitmproxy.py -o html report.html

``-o html`` tells HTTPolice to produce :doc:`HTML reports <reports>`
(omit it if you want a plain text report).
Finally, ``report.html`` is the name of the output file.

Now, mitmproxy/mitmdump starts up as usual.
As it intercepts requests and responses,
it feeds them to HTTPolice for checking.
When you stop mitmdump (Ctrl+C) or exit mitmproxy,
HTTPolice writes an HTML report to ``report.html``.
