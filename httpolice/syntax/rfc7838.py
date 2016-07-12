# -*- coding: utf-8; -*-

# pylint: disable=import-error
# (for `six.moves`; can't fit on the same line due to interference from isort)

from httpolice.util.moves import unquote_to_bytes as pct_decode
from six.moves.urllib.parse import quote as pct_encode

import six

from httpolice.citation import RFC
from httpolice.parse import (can_complain, fill_names, literal, many,
                             maybe_str, pivot, simple_parse, skip, subst)
from httpolice.structure import AltSvcParam, MultiDict, Parametrized
from httpolice.syntax.rfc7230 import (OWS, comma_list1, port, quoted_string,
                                      tchar, token, uri_host)
from httpolice.syntax.rfc7234 import delta_seconds
from httpolice.util.text import force_bytes, force_unicode


# pylint: enable=import-error


clear = literal('clear', case_sensitive=True)                           > pivot

@can_complain
def _check_protocol_id(complain, encoded_id):
    # Since there is only one correct way to encode
    # an ALPN protocol ID into an RFC 7838 ``protocol-id``,
    # we just compute it and compare to what's in the message.
    decoded_id = pct_decode(force_bytes(encoded_id))
    correct_encoded_id = u''
    for b in six.iterbytes(decoded_id):
        c = six.int2byte(b)
        if (tchar - '%').match(c):
            correct_encoded_id += force_unicode(c)
        else:
            correct_encoded_id += pct_encode(c, safe='').upper()
    if encoded_id != correct_encoded_id:
        complain(1256, actual=encoded_id, correct=correct_encoded_id)
    return decoded_id

protocol_id = _check_protocol_id << token                               > pivot

@can_complain
def _check_alt_authority(complain, value):
    return simple_parse(value,
                        maybe_str(uri_host) + ':' + port,
                        complain, 1257, authority=value)

alt_authority = _check_alt_authority << quoted_string                   > pivot

alternative = protocol_id * skip('=') * alt_authority                   > pivot
parameter = ((AltSvcParam << token) *
             skip('=') * (token | quoted_string))                       > pivot
alt_value = Parametrized << (
    alternative *
    (MultiDict << many(skip(OWS * ';' * OWS) * parameter)))             > pivot

Alt_Svc = clear | comma_list1(alt_value)                                > pivot

ma = delta_seconds                                                      > pivot
persist = subst(True) << literal('1')                                   > pivot

Alt_Used = uri_host + maybe_str(':' + port)                             > pivot


fill_names(globals(), RFC(7838))
