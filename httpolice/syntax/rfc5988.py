# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import (auto, can_complain, fill_names, literal, many,
                             maybe, named, pivot, skip, string, string1)
from httpolice.structure import (CaseInsensitive, MediaType, MultiDict,
                                 Parametrized, RelationType)
from httpolice.syntax.common import ALPHA, DIGIT, HTAB, SP, VCHAR
from httpolice.syntax.rfc2616 import LOALPHA
from httpolice.syntax.rfc3986 import URI, URI_reference as URI_Reference
from httpolice.syntax.rfc5646 import Language_Tag
from httpolice.syntax.rfc5987 import ext_value, parmname__excluding
from httpolice.syntax.rfc6838 import subtype_name, type_name
from httpolice.syntax.rfc7230 import OWS, comma_list, quoted_string


# RFC 5988 refers to HTML 4.01 for the ``MediaDesc`` rule,
# but HTML 4.01 doesn't actually define a grammar for that;
# it only gives a vague idea of what it is supposed to be.
# So we use a fairly permissive form.
# Also, from RFC 5988 Section 5.4:
# "its value MUST be quoted if it contains a semicolon (';') or comma (',')".

_MediaDesc = string((VCHAR | HTAB | SP) - literal('"'))
_MediaDesc_no_delim = string((VCHAR | HTAB | SP) -
                             literal('"') - literal(';') - literal(','))


# This has been slightly adapted to the rules of RFC 7230.
# The ``OWS`` are derived from the "implied ``*LWS``" requirement.

ptokenchar = (literal('!') | '#' | '$' | '%' | '&' | "'" | '(' |
              ')' | '*' | '+' | '-' | '.' | '/' | DIGIT |
              ':' | '<' | '=' | '>' | '?' | '@' | ALPHA |
              '[' | ']' | '^' | '_' | '`' | '{' | '|' |
              '}' | '~')                                                > auto
ptoken = string1(ptokenchar)                                            > auto

media_type = MediaType << type_name + '/' + subtype_name                > pivot
quoted_mt = skip('"') * media_type * skip('"')                          > pivot

reg_rel_type = RelationType << (
    LOALPHA + string(LOALPHA | DIGIT | '.' | '-'))                      > auto
ext_rel_type = URI                                                      > auto
relation_type = reg_rel_type | ext_rel_type                             > pivot
relation_types = (
    (lambda x: [x]) << relation_type |
    skip('"' * OWS) *
    (relation_type % many(skip(string1(SP)) * relation_type)) *
    skip(OWS * '"'))                                                    > pivot

def ext_name_star__excluding(exclude):
    return (parmname__excluding(exclude) + '*'
            > named(u'ext-name-star', RFC(5988)))

_builtin_params = {
    'rel': relation_types,
    'anchor': skip('"' * OWS) * URI_Reference * skip(OWS * '"'),
    'rev': relation_types,
    'hreflang': Language_Tag,
    'media': (_MediaDesc_no_delim |
              skip('"' * OWS) * _MediaDesc * skip(OWS * '"')),
    'title': quoted_string,
    'title*': ext_value,
    'type': (media_type | quoted_mt),
}

def link_extension(exclude_builtin):
    if exclude_builtin:
        exclude1 = [name for name in _builtin_params if not name.endswith('*')]
        exclude2 = [name.rstrip('*')
                    for name in _builtin_params if name.endswith('*')]
    else:       # pragma: no cover
        exclude1 = exclude2 = None
    return (
        (
            (CaseInsensitive << parmname__excluding(exclude1)) *
            maybe(skip(OWS * '=' * OWS) * (ptoken | quoted_string))
        ) |
        (
            (CaseInsensitive << ext_name_star__excluding(exclude2)) *
            skip(OWS * '=' * OWS) * ext_value
        )
    ) > named(u'link-extension', RFC(5988), is_pivot=True)

link_param = link_extension(exclude_builtin=True)
for _name, _rule in _builtin_params.items():
    link_param = link_param | ((CaseInsensitive << literal(_name)) *
                               skip(OWS * '=' * OWS) * _rule)
link_param = link_param                                                 > pivot

@can_complain
def _process_params(complain, params):
    r = []
    seen = set()
    for (name, value) in params:
        if name in seen:
            # The spec says "occurrences after the first must be ignored"
            # for ``rel``, ``title``, and ``title*``,
            # but not for ``media`` and ``type``.
            if name in [u'rel', u'title', u'title*']:
                complain(1225, name=name)
                continue
            elif name in [u'media', u'type']:
                complain(1225, name=name)
        seen.add(name)
        r.append((name, value))
        if name == u'rev':
            complain(1226)
    return MultiDict(r)

link_value = Parametrized << (
    skip('<') * URI_Reference * skip('>') *
    (_process_params << many(skip(OWS * ';' * OWS) * link_param)))      > pivot

Link = comma_list(link_value)                                           > pivot


fill_names(globals(), RFC(5988))
