Django integration
==================

.. highlight:: console

HTTPolice has a package for integrating with Django 1.8+::

  $ pip install Django-HTTPolice

.. highlight:: py

This package provides :class:`django_httpolice.HTTPoliceMiddleware`.
Add it to your `MIDDLEWARE_CLASSES`, as close to the top as possible::

  MIDDLEWARE_CLASSES = [
      'django_httpolice.HTTPoliceMiddleware',
      'django.middleware.common.CommonMiddleware',
      # ...
  ]

By default, this middleware does nothing if ``DEBUG = False``.
You can override this by setting `HTTPOLICE_ENABLE` to `True` or `False`.

When enabled, the middleware checks all exchanges passing through it,
and stores them in a global variable called the *backlog*.
The size of the backlog is capped by the `HTTPOLICE_BACKLOG` setting,
which defaults to 20 exchanges.

Note that the backlog is stored in process memory,
so it is cleared every time Django’s development server reloads itself.

The second part of the package is :func:`django_httpolice.report_view`.
Add it to your URLconf like this::

  import django_httpolice
  
  urlpatterns = [
      # ...
      url(r'^httpolice/$', django_httpolice.report_view),
      # ...
  ]

You may want to include or exclude this URL pattern
based on your `DEBUG` setting.

Now, start the server and open ``/httpolice/`` (or your URL)
to see an HTML report on all the exchanges currently in the backlog.
The **latest** exchanges are shown at the **top** of the report.
