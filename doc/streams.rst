Analyzing raw TCP streams
=========================

.. highlight:: console

An obvious way to capture HTTP requests and responses
is to dump them with a `network sniffer`__.
This only works for cleartext connections (without TLS encryption),
but on the other hand, you don’t need to change your clients or servers.

__ https://en.wikipedia.org/wiki/Packet_analyzer

HTTPolice can parse HTTP/1.x streams from the ground up.
Parsing HTTP/2 is not yet supported.


Using tcpflow
-------------
You may be familiar with `tcpdump`__, but it won’t work:
HTTPolice needs the reassembled TCP streams, not individual packets.
You can get these streams with a tool called `tcpflow`__::

  $ mkdir dump

  $ cd dump/

  $ sudo tcpflow -T'%t-%A-%a-%B-%b-%#' port 80
  tcpflow: listening on wlp4s0

__ https://en.wikipedia.org/wiki/Tcpdump
__ https://github.com/simsong/tcpflow

(Note the ``-T`` option—it is necessary to get the right output.)

tcpflow starts capturing all connections to or from TCP port 80.
For example, you can launch a Web browser and go to an ‘http:’ site.
Once you are done, exit the browser, then stop tcpflow with Ctrl+C.
(It is important that connections are closed before tcpflow shuts down,
otherwise they may be incomplete.)

Now you have one or more pairs of stream files::

  $ ls
  1469847441-054.175.219.008-00080-172.016.000.100-38656-0  report.xml
  1469847441-172.016.000.100-38656-054.175.219.008-00080-0

Tell HTTPolice to read this directory with the ``tcpflow`` input format::

  $ httpolice -i tcpflow .

HTTPolice will combine the files into pairs based on their filenames.
Due to a `limitation in tcpflow`__, this only works if
every combination of source+destination address+port is unique.
If there are duplicates, you will get an error.

__ https://github.com/simsong/tcpflow/issues/128

It’s OK if you capture some streams that are not HTTP/1.x.
HTTPolice will just complain with notices such as `1279`__.
This means you can run tcpflow without a filter, capturing *all* TCP traffic
on a given network interface, and then let HTTPolice sort it out
while :ref:`silencing <silence>` those notices::

  $ sudo tcpflow -T'%t-%A-%a-%B-%b-%#'

  $ httpolice -i tcpflow -o html -s 1279 . >../report.html

__ http://httpolice.readthedocs.io/page/notices.html#1279

Using tcpick
------------
`tcpick`__ is another tool for reassembling TCP streams.
It doesn’t have the “unique port” limitation of tcpflow,
but it has a different problem:
sometimes it produces files that are clearly invalid HTTP streams
(HTTPolice will fail to parse them with notices like `1009`__).

__ http://tcpick.sourceforge.net/
__ http://httpolice.readthedocs.io/page/notices.html#1009

Anyway, using it is very similar to using tcpflow::

  $ mkdir dump

  $ cd dump/

  $ sudo tcpick -wR -F2 'port 80'
  Starting tcpick 0.2.1 at 2016-07-30 06:14 MSK
  Timeout for connections is 600
  tcpick: listening on wlp4s0
  setting filter: "port 80"
  [...]
  ^C
  3837 packets captured
  30 tcp sessions detected

  $ httpolice -i tcpick .

(Note the ``-wR -F2`` options.)


Other sniffers
--------------
If you use some other tool to capture the TCP streams,
use the ``streams`` input format to pass pairs of files::

  $ httpolice -i streams requests1.dat responses1.dat requests2.dat ...

Or ``req-stream`` if you only have request streams::

  $ httpolice -i req-stream requests1.dat requests2.dat ...

Or ``resp-stream`` if you only have response streams
(:ref:`not recommended <exchanges>`)::

  $ httpolice -i resp-stream responses1.dat responses2.dat ...

Note that ``resp-stream`` may not work at all
if any of the requests are `HEAD`__,
because responses to HEAD are `parsed differently`__.

__ https://tools.ietf.org/html/rfc7231#section-4.3.2
__ https://tools.ietf.org/html/rfc7230#section-3.3.3


Combined format
---------------
.. highlight:: none

Sometimes you want to compose an HTTP exchange by hand, to test something.
To make this easier, there’s a special input format
that combines the request and response streams into one file::

  The lines at the beginning are ignored.
  You can use them for comments.
  
  ======== BEGIN INBOUND STREAM ========
  GET / HTTP/1.1
  Host: example.com
  User-Agent: demo
  
  ======== BEGIN OUTBOUND STREAM ========
  HTTP/1.1 200 OK
  Date: Thu, 31 Dec 2015 18:26:56 GMT
  Content-Type: text/plain
  Connection: close
  
  Hello world!

It must be saved with **CRLF (Windows)** line endings.

Also, for this format, the filename suffix (extension) is important.
If it is ``.https``, the request URI is assumed to have an ``https:`` scheme.
If it is ``.noscheme``, the scheme is unknown.
Otherwise, the ``http:`` scheme is assumed.

.. highlight:: console

Now, tell HTTPolice to use the ``combined`` format::

  $ httpolice -i combined exchange1.txt

More examples can be found in HTTPolice’s `test suite`__.

__ https://github.com/vfaronov/httpolice/tree/master/test/combined_data
