How to hack on HTTPolice
========================

Development environment
~~~~~~~~~~~~~~~~~~~~~~~
Set up::

  $ virtualenv /path/to/env
  $ source /path/to/env/bin/activate
  $ pip install -e .
  $ pip install -r tools/requirements.txt
  $ pip install ...    # any extra tools you like to have

Run tests::

  $ py.test

Run Pylint::

  $ tools/pylint_all.sh -j 2
  $ # ... or selectively:
  $ pylint httpolice/response.py

Use isort if you like -- there's an ``.isort.cfg`` with the right options --
but this is not enforced automatically for now.

You may also want to use linters for HTML, CSS, and JS (see ``.travis.yml``).


Dependencies
------------
Versions of development tools (py.test, Pylint...)
are pinned down to help make builds/QA reproducible.
From time to time, they are manually upgraded::

  $ pip-compile tools/requirements.in
  $ pip install -r tools/requirements.txt
  $ # ... check that everything is OK with the new versions
  $ # ... maybe some Pylint overrides are no longer necessary
  $ git add tools/requirements.txt && git commit

Eventually I will use pip-sync for this,
but right now it is unusable due to `pip-tools issue #206`__.

__ https://github.com/nvie/pip-tools/issues/206


Codebase overview and caveats
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rules and magic
---------------
At the core of HTTPolice are four long functions:

- ``httpolice.message.check_message``
- ``httpolice.request.check_request``
- ``httpolice.response.check_response_itself``
- ``httpolice.response.check_response_in_context``

Code in these functions looks a bit like rules in an expert system.
Most of these rules are ad-hoc (corresponding directly to text in the RFCs),
self-explanatory (by reference to the notice IDs they produce),
and independent of each other.
There is no need to split them into smaller functions.

The important thing about these rules is that they utilize a rich domain model
defined mostly in ``httpolice.structure`` and ``httpolice.headers``.
This provides magic, such as in ``Parametrized`` and ``HeaderView``,
that makes the rules look very natural and easy to follow.
However, **you have to know and keep in mind** how this magic actually works,
otherwise it's easy to introduce bugs.


``None`` and ``Unavailable``
----------------------------
Many things in the domain model can have the special values
``None`` and/or ``httpolice.structure.Unavailable``
in addition to the normal range of their types.
Usually:

- ``None`` means "we have no information about this thing";
- ``Unavailable`` means "we know that this thing is present
  (not missing), but we don't know its value".

For example:

- ``httpolice.Message.body`` can be:

  - a non-empty bytestring;
  - an empty bytestring, meaning that the body was absent or empty
    (RFC 7230 distinguishes between absent and empty, but we don't);
  - ``Unavailable``, meaning that the body was present but unknown
    (for instance, HAR files never contain the raw payload body,
    only the ``Message.decoded_body``);
  - ``None``, meaning that we have no idea if there was or wasn't a body.

- ``httpolice.known.method.is_idempotent`` can return:

  - ``True``, which means "definitely is";
  - ``False``, which means "definitely is not";
  - ``None``, which means "don't know"

  (this is why you see comparisons to ``False`` all over the place).
