How to hack on HTTPolice
========================

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
This provides magic, such as in ``Parametrized`` and ``SingleHeaderView``,
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
