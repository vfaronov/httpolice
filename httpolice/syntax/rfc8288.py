# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import (auto, can_complain, fill_names, literal, many,
                             mark, maybe, parse, pivot, skip, string, string1)
from httpolice.structure import (CaseInsensitive, MediaType, MultiDict,
                                 Parametrized)
from httpolice.syntax.common import DIGIT, SP, check_media_type
from httpolice.syntax.rfc2616 import LOALPHA
from httpolice.syntax.rfc3986 import URI, URI_reference as URI_Reference
from httpolice.syntax.rfc5646 import Language_Tag
from httpolice.syntax.rfc6838 import subtype_name, type_name
from httpolice.syntax.rfc7230 import BWS, OWS, comma_list, quoted_string, token
from httpolice.syntax.rfc8187 import ext_value


@can_complain
def _process_params(complain, params):
    r = []
    seen = set()
    for (name, value) in params:
        if name in [u'rel', u'media', u'title', u'title*', u'type']:
            if name in seen:
                complain(1225, name=name)
                # "occurrences after the first MUST be ignored by parsers"
                continue
            seen.add(name)
        if value is not None:
            (parsed_as, value) = value
        if name == u'title' and parsed_as is token:
            complain(1307)
        if name == u'hreflang' and parsed_as is quoted_string:
            complain(1308)
        symbol = {
            u'anchor': URI_Reference, u'rel': rel, u'rev': rev,
            u'hreflang': hreflang, u'type': type_, u'title*': ext_value,
        }.get(name)
        if symbol is not None:
            value = parse(value, symbol, complain, 1158,
                          name=name, value=value)
        r.append((name, value))
        if name == u'rev':
            complain(1226)
    if u'rel' not in seen:
        complain(1309)
    return MultiDict(r)

link_param = (
    (CaseInsensitive << token) * skip(BWS) *
    maybe(skip(literal('=') * BWS) * (mark(token) |
                                      mark(quoted_string))))            > pivot

link_value = Parametrized << (
    skip('<') * URI_Reference * skip('>') *
    (_process_params << many(skip(OWS * ';' * OWS) * link_param)))      > pivot

Link = comma_list(link_value)                                           > pivot


anchor = URI_Reference                                                  > auto

reg_rel_type = CaseInsensitive << (
    LOALPHA + string(LOALPHA | DIGIT | '.' | '-'))                      > auto
ext_rel_type = URI                                                      > auto
relation_type = reg_rel_type | ext_rel_type                             > pivot
rel = rev = relation_type % many(skip(string1(SP)) * relation_type)     > auto

hreflang = Language_Tag                                                 > auto

type_ = check_media_type << (
    MediaType << type_name + '/' + subtype_name)                        > auto


fill_names(globals(), RFC(8288))
