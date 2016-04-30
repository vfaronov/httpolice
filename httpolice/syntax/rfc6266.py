# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import auto, fill_names, literal, many, pivot, skip
from httpolice.structure import CaseInsensitive, MultiDict, Parametrized
from httpolice.syntax.rfc2616 import value
from httpolice.syntax.rfc5987 import ext_value
from httpolice.syntax.rfc7230 import OWS, token, token__excluding


# This has been slightly adapted to the rules of RFC 7230.
# The ``OWS`` are derived from the "implied ``*LWS``" requirement.


# We have no need to special-case "inline" and "attachment", simplify.
disposition_type = CaseInsensitive << token                             > pivot

filename_parm = (
    (CaseInsensitive << literal('filename')) *
    skip(OWS * '=' * OWS) * value |
    (CaseInsensitive << literal('filename*')) *
    skip(OWS * '=' * OWS) * ext_value)                                  > pivot

# ``token`` is a superset of ``ext-token``,
# and special-casing ``ext-token`` requires
# something more complex than our `string_excluding`.
# Until then, we can simplify a bit.
disp_ext_parm = (
    (CaseInsensitive << token__excluding(['filename', 'filename*'])) *
    skip(OWS * '=' * OWS) * value)                                      > pivot

disposition_parm = filename_parm | disp_ext_parm                        > auto

content_disposition = Parametrized << (
    disposition_type *
    (MultiDict << many(skip(OWS * ';' * OWS) * disposition_parm)))      > pivot


fill_names(globals(), RFC(6266))
