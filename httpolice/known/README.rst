How to work with these CSV files
================================

They are in the Excel (RFC 4180) dialect. Any decent tool should be able
to deal with them. But pay attention to line endings -- they should be LF.

When editing a larger table such as ``header.csv``, it may be necessary to:

- resize the ``comment`` column

  - in LibreOffice Calc, right-click on the column header, select `Column
    Width`, and set something like 5"

- lock down the first row and column

  - in LibreOffice Calc, put the cursor on the B2 cell, then select `View` →
    `Freeze Rows and Columns`


Common fields
-------------

``title``
    Will be displayed in mouseover tooltips.

``comment``
    Can be used for arbitrary comments, not shown to the user.

``no_sync``
    See ``tools/iana.py``.

``rfc``, ``rfc_section``, ``rfc_appendix``
    Defines an RFC citation. Cannot be used together with ``cite_url``.

``cite_url``, ``cite_title``
    Defines an arbitrary citation. Cannot be used together with ``rfc``.


Syntax-related fields
~~~~~~~~~~~~~~~~~~~~~

``syntax_module``, ``syntax_symbol``
    Together identify the name under ``httpolice.syntax`` that will be resolved
    to get the ``httpolice.parse.Symbol`` that can parse this syntax.

``argument``
    Whether the directive/parameter can or must have an argument.


``header.csv``
--------------

``rule``
    Defines how to combine and represent the parsed values of this header.
    For typical headers, set this to ``multi`` if the header is defined
    as a comma-separated list, otherwise to ``single``. For headers that need
    custom processing, set this to ``special`` and add an appropriate
    ``HeadersView.special_case`` in ``httpolice.header``.

``for_request``, ``for_response``
    Whether this header can appear in requests and responses, respectively.

``precondition``
    Whether this header is a precondition (RFC 7232).

``proactive_conneg``
    Whether this header is for proactive content negotiation (RFC 7231
    Section 5.3).

``bad_for_connection``
    You can set this to ``True`` if the presence of this header
    in a ``Connection`` header should trigger notice 1034.

``bad_for_trailer``
    You can set this to ``True`` if the presence of this header in a trailer
    should trigger notice 1026.

``iana_status``
    Filled by ``tools/iana.py``. You should not need to change it.


``media_type.csv``
------------------

``patch``
    Whether this media type is a patch, usable with the PATCH method
    (as in notice 1213).

``is_json``
    Set this to ``True`` if the media type uses JSON syntax but does **not**
    end with ``+json``.

``is_xml``
    Set this to ``True`` if the media type uses XML syntax but does **not** end
    with ``+xml``.

``deprecated``
    Filled by ``tools/iana.py``. You should not need to change it.


``method.csv``
--------------

``defines_body``
    Whether a meaning is defined for a payload body with this method.
    (For example, RFC 7231 Section 4.3.1 says "a payload within a GET request
    message has no defined semantics", so ``defines_body`` is ``False``.)

``cacheable``
    Whether responses to this method can be cached (RFC 7234).
