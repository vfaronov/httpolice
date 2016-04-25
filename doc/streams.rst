Analyzing raw TCP streams
=========================

.. highlight:: console

An obvious way to capture HTTP requests and responses
is to dump them with a `network sniffer`__.
This only works for cleartext connections (without TLS encryption),
but on the other hand, you don’t need to change your clients or servers.

__ https://en.wikipedia.org/wiki/Packet_analyzer

HTTPolice can parse HTTP/1.x streams from the ground up.
HTTP/2 is not yet supported.

You may be familiar with `tcpdump`__, but it won’t work:
HTTPolice needs the raw TCP streams—just the data sent or received.
There are two Unix tools to dump TCP streams: `tcpick`__ and `tcpflow`__.
Unfortunately, both **sometimes produce incorrect files**,
so this may not be 100% reliable.

__ https://en.wikipedia.org/wiki/Tcpdump
__ http://tcpick.sourceforge.net/
__ https://github.com/simsong/tcpflow


tcpick
------
I have had more success with tcpick.
Here’s how it can be used::

  $ mkdir dump

  $ cd dump/

  $ sudo tcpick -wR 'port 80'
  Starting tcpick 0.2.1 at 2016-04-13 05:11 MSK
  Timeout for connections is 600
  tcpick: listening on wlp4s0
  setting filter: "port 80"

tcpick starts capturing all connections to or from TCP port 80.
For example, you can launch a Web browser and go to an ‘http:’ site.
Once you are done, exit the browser, then stop tcpick with Ctrl+C.
(It is important that connections are closed before tcpick shuts down,
otherwise they may be incomplete.)

Now you have one or more pairs of files in this directory::

  $ ls
  tcpick_172.16.0.102_185.72.247.137_http.clnt.dat
  tcpick_172.16.0.102_185.72.247.137_http.serv.dat

Then you tell HTTPolice to use the ``tcpick`` input format::

  $ httpolice -i tcpick .


tcpflow
-------
Very similar to tcpick::

  $ mkdir dump

  $ cd dump/

  $ sudo tcpflow -T'%t-%#-%A-%B' port 80
  tcpflow: listening on wlp4s0
  ^Ctcpflow: terminating

  $ ls
  1460513796-0-172.016.000.102-185.072.247.137  alerts.txt
  1460513796-0-185.072.247.137-172.016.000.102  report.xml

  $ httpolice -i tcpflow .

The cryptic ``-T`` option is necessary to get the right filenames.


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
