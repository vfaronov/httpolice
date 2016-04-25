Quickstart
==========

.. highlight:: console


Installation
------------
HTTPolice is a Python package that can be installed with pip
(on Python 2.7 or 3.4+)::

  $ pip install HTTPolice

If you’re not familiar with pip, check the :doc:`install` section.


Using HAR files
---------------
Let’s start with something easy.

If you’re running Google Chrome, Firefox, or Microsoft Edge,
you can use their developer tools to export HTTP requests and responses
as a `HAR file`__, which can then be analyzed by HTTPolice.

__ https://en.wikipedia.org/wiki/.har

For example, in Firefox,
press F12 to open the toolbox, and switch to its Network pane.
Then, open a simple Web site—let’s try `jshint.com`__.
All HTTP exchanges made by the browser appear in the Network pane.
Right-click inside that pane and select “Save All As HAR”.

__ http://jshint.com/

Now that you have the HAR file, you can feed it into HTTPolice::

  $ httpolice -i har /path/to/file.har
  ------------ request 6 : GET /ga.js
  ------------ response 6 : 200 OK
  C 1035 Deprecated media type text/javascript
  D 1168 Response from cache
  ------------ request 7 : GET /r/__utm.gif?utmwv=5.6.7&utm...
  ------------ response 7 : 200 OK
  E 1108 Wrong day of week in Expires
  C 1162 Pragma: no-cache in a response


Better reports
--------------
By default, HTTPolice prints a simple text report
which may be hard to understand.
Use the ``-o html`` option to make a detailed HTML report instead.
You will also need to redirect it to a file::

  $ httpolice -i har -o html /path/to/file.har >report.html

Open ``report.html`` in your Web browser and enjoy.


Using mitmproxy
---------------
What if you have an HTTP API that is accessed by special clients?
Let’s say curl is special enough::

  $ curl -ksiX POST https://eve-demo.herokuapp.com/people \
  >   -H 'Content-Type: application/json' \
  >   -d '{"firstname":"John", "lastname":"Smith"}'
  HTTP/1.1 201 CREATED
  Connection: keep-alive
  Content-Type: application/json
  Content-Length: 279
  Server: Eve/0.6.1 Werkzeug/0.10.4 Python/2.7.4
  Date: Mon, 25 Apr 2016 09:21:32 GMT
  Via: 1.1 vegur
  
  {"_links": {"self": {"href": "people/571de19c4fd7bd0003356826", "title": "person"}}, "_etag": "3b1f9c356f87a615645e2e51f8d3e05e0e462c03", "_id": "571de19c4fd7bd0003356826", "_created": "Mon, 25 Apr 2016 09:21:32 GMT", "_updated": "Mon, 25 Apr 2016 09:21:32 GMT", "_status": "OK"}

How do you get this into HTTPolice?

One way is to use `mitmproxy`__,
an advanced tool for intercepting HTTP traffic.
You can install it `manually`__,
or from your distribution’s packages if they are recent enough
(0.15 should work).

__ https://mitmproxy.org/
__ http://docs.mitmproxy.org/en/stable/install.html

We’re going to use mitmproxy’s command-line tool—`mitmdump`__.
The following command will start mitmdump as an HTTP proxy on port 8080
with HTTPolice integration::

  $ mitmdump -s "`python -m httpolice.plus.mitmproxy` -o html report.html"

__ http://docs.mitmproxy.org/en/latest/mitmdump.html

With mitmdump running, tell curl to use it as a proxy::

  $ curl -x localhost:8080 \
  >   -ksiX POST https://eve-demo.herokuapp.com/people \
  >   -H 'Content-Type: application/json' \
  >   -d '{"firstname":"John", "lastname":"Williams"}'

In the output of mitmdump, you will see that it has intercepted the exchange.
Now, when you stop mitmdump (Ctrl+C),
HTTPolice will write an HTML report to ``report.html``.


More options
------------
There are other ways to get your data into HTTPolice.
Check the :doc:`full manual <index>`.
