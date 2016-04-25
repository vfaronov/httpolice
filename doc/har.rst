Analyzing HAR files
===================

.. highlight:: console

`HAR`__ is a quasi-standardized JSON format for saving HTTP traffic.
It is supported by many HTTP-related tools,
including developer consoles of some Web browsers.

__ https://en.wikipedia.org/wiki/.har

HTTPolice can analyze HAR files with the ``-i har`` option::

  $ httpolice -i har myfile.har

However, please note that HAR support in major Web browsers is **erratic**.
HTTPolice tries to do a reasonable job
on files exported from Chrome, Firefox, and Edge,
but some information is simply lost.

If HTTPolice fails on your HAR files,
feel free to `submit an issue`__ (don’t forget to attach the files),
and I’ll see what can be done about it.

__ https://github.com/vfaronov/httpolice/issues
