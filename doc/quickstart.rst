Quickstart
==========

.. highlight:: console


Installation
------------
HTTPolice is a Python package that can be installed with pip
(on Python 2.7 or 3.4+)::

  $ pip install HTTPolice

If you’re not familiar with pip, check the manual’s :doc:`install` section.


Using HAR files
---------------
Let’s start with something easy.

If you’re running Google Chrome, Firefox, or Microsoft Edge,
you can use their developer tools to export HTTP requests and responses
as a `HAR file`__, which can then be analyzed by HTTPolice.

__ https://en.wikipedia.org/wiki/.har

For example, in Firefox,
press F12 to open the toolbox, and switch to its Network pane.
Then, open a simple Web site—let’s try `Mark Nottingham’s page`__.
All HTTP exchanges made by the browser appear in the Network pane.
Right-click inside that pane and select “Save All As HAR”.

__ https://www.mnot.net/

Then feed this HAR file to HTTPolice::

  $ httpolice -i har /path/to/file.har 
  ------------ request: GET /1441/25776044114_0e5b9879a0_z.jpg
  ------------ response: 200 OK
  C 1277 Obsolete 'X-' prefix in X-Photo-Farm
  C 1277 Obsolete 'X-' prefix in X-Photo-Origin
  E 1000 Malformed Expires header
  E 1241 Date + Age is in the future


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

.. note::

   Another solution would be to use `Fiddler`__.
   Especially Windows users may find it easier.
   Use Fiddler’s `HAR 1.2 export`__ to get the data into HTTPolice.

   __ http://www.telerik.com/fiddler
   __ http://docs.telerik.com/fiddler/KnowledgeBase/ImportExportFormats

You’ll need the integration package::

  $ pip install mitmproxy-HTTPolice

Now, we’re going to use mitmproxy’s command-line tool—`mitmdump`__.
The following command will start mitmdump as an HTTP proxy on port 8080
with HTTPolice integration::

  $ mitmdump -s "`python -m mitmproxy_httpolice` -o html report.html"

__ http://docs.mitmproxy.org/en/latest/mitmdump.html

With mitmdump running, tell curl to use it as a proxy::

  $ curl -x localhost:8080 \
  >   -ksiX POST https://eve-demo.herokuapp.com/people \
  >   -H 'Content-Type: application/json' \
  >   -d '{"firstname":"John", "lastname":"Williams"}'

In the output of mitmdump, you will see that it has intercepted the exchange.
Now, when you stop mitmdump (Ctrl+C),
HTTPolice will write an HTML report to ``report.html``.


Django integration
------------------
Suppose you’re building a Web application with `Django`__ (1.8+).
You probably have a test suite
that makes requests to your app and checks responses.
You can easily instrument this test suite with HTTPolice
and get instant feedback when you break the protocol.

__ https://www.djangoproject.com/

::

  $ pip install Django-HTTPolice

.. highlight:: py

Add the HTTPolice middleware to the top of your middleware list::

  MIDDLEWARE_CLASSES = [
      'django_httpolice.HTTPoliceMiddleware',
      'django.middleware.common.CommonMiddleware',
      # ...
  ]

Add a couple settings::

  HTTPOLICE_ENABLE = True
  HTTPOLICE_RAISE = True

.. highlight:: console

Now let’s run the tests and see what’s broken::

  $ python manage.py test
  .E.
  ======================================================================
  ERROR: test_get_plain (example_app.test.ExampleTestCase)
  ----------------------------------------------------------------------
  Traceback (most recent call last):
    [...]
    File "[...]/django_httpolice/middleware.py", line 81, in process_response
      raise ProtocolError(exchange)
  django_httpolice.common.ProtocolError: HTTPolice found errors in this response:
  ------------ request: GET /api/v1/?name=Martha&format=plain
  C 1070 No User-Agent header
  ------------ response: 200 OK
  E 1038 Bad JSON body
  
  
  ----------------------------------------------------------------------
  Ran 3 tests in 0.351s
  
  FAILED (errors=1)

In `this example`__, the app sent a wrong ``Content-Type`` header
and HTTPolice caught it.

__ https://github.com/vfaronov/django-httpolice/blob/234aa3a/example/example_app/views.py#L16


More options
------------
There are other ways to get your data into HTTPolice.
Check the :doc:`full manual <index>`.
