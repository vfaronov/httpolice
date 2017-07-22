HTTPolice user manual
=====================

`HTTPolice`__ is a validator or “linter” for HTTP requests and responses.
It can spot bad header syntax, inappropriate status codes, and other potential
problems in your HTTP server or client.

__ https://github.com/vfaronov/httpolice

This manual explains all features of HTTPolice in detail.
For a hands-on introduction, jump to the :doc:`quickstart`.

Contents
--------

.. toctree::
   :maxdepth: 2

   quickstart
   install
   concepts
   streams
   har
   reports
   api
   history


Supplementary documents
-----------------------

- `List of all notices`__ that HTTPolice can output
- `Example report`__ produced by HTTPolice

__ notices.html
__ showcase.html


Integration packages
--------------------

- `mitmproxy integration`__
- `Django integration`__
- `Chrome extension`__ (third-party)

__ http://mitmproxy-httpolice.readthedocs.io/
__ http://django-httpolice.readthedocs.io/
__ https://chrome.google.com/webstore/detail/httpolice-devtool/hnlnhebgfcfemjaphgbeokdnfpgbnhgn
