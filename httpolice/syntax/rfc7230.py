# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import (auto, can_complain, fill_names, group, literal,
                             many, maybe, maybe_str, named, octet, octet_range,
                             pivot, recursive, skip, string, string1,
                             string_excluding, string_times, subst)
from httpolice.structure import (CaseInsensitive, ConnectionOption, FieldName,
                                 Method, MultiDict, Parametrized,
                                 TransferCoding, UpgradeToken, Versioned)
from httpolice.syntax.common import ALPHA, DIGIT, DQUOTE, HTAB, SP, VCHAR
from httpolice.syntax.rfc3986 import (absolute_URI, authority,
                                      host as uri_host, port, query,
                                      relative_part, segment)


obs_text = octet_range(0x80, 0xFF)                                      > auto

tchar = (literal('!') | '#' | '$' | '%' | '&' | "'" | '*' | '+' | '-' | '.' |
         '^' | '_' | '`' | '|' | '~' | DIGIT | ALPHA)                   > auto

token = string1(tchar)                                                  > auto

def token__excluding(excluding):
    return string_excluding(tchar, [''] + list(excluding))

def quoted_pair(sensible_for):
    # In RFC 7230, ``<quoted-pair>`` is a single rule,
    # but we parametrize it to report no. 1017 depending on the context.
    @can_complain
    def check_sensible(complain, c):
        if c not in sensible_for:
            complain(1017, char=c)
        return c
    return (check_sensible << skip('\\') * (HTAB | SP | VCHAR | obs_text)
            > named(u'quoted-pair', RFC(7230)))

qdtext = (HTAB | SP | octet(0x21) | octet_range(0x23, 0x5B) |
          octet_range(0x5D, 0x7E) | obs_text)                           > auto
quoted_string = (skip(DQUOTE) *
                 string(qdtext | quoted_pair(sensible_for=u'"\\')) *
                 skip(DQUOTE))                                          > auto

ctext = (HTAB | SP | octet_range(0x21, 0x27) | octet_range(0x2A, 0x5B) |
         octet_range(0x5D, 0x7E) | obs_text)                            > auto

def comment(include_parens=False):
    inner = recursive() > named(u'comment', RFC(7230))
    inner.rec = '(' + string(ctext | quoted_pair(sensible_for=u'()\\') |
                             inner) + ')'
    if not include_parens:
        inner = (lambda s: s[1:-1]) << inner
    return inner > named(u'comment', RFC(7230))

OWS = string(SP | HTAB)                                                 > auto

@can_complain
def _check_just_one_space(complain, s):
    if s != ' ':
        complain(1014, num=len(s))
    return s

RWS = _check_just_one_space << string1(SP | HTAB)                       > auto

@can_complain
def _bad_whitespace(complain, s):
    if s:
        complain(1015)
    return s

BWS = _bad_whitespace << OWS                                            > auto

@can_complain
def _collect_elements(complain, xs):
    if xs is None:
        xs = []
    r = [elem for elem in xs if elem is not None]
    if len(r) != len(xs):
        complain(1151)
    return r

def comma_list(element):
    return _collect_elements << maybe(
        (subst([None, None]) << literal(',') |
         (lambda x: [x]) << group(element)) +
        many(skip(OWS * ',') * maybe(skip(OWS) * element))
    ) > named(u'#rule', RFC(7230, section=u'7'))

def comma_list1(element):
    return _collect_elements << (
        many(subst(None) << ',' * OWS) +
        ((lambda x: [x]) << group(element)) +
        many(skip(OWS * ',') * maybe(skip(OWS) * element))
    ) > named(u'1#rule', RFC(7230, section=u'7'))

method = Method << token                                                > pivot

absolute_path = string1('/' + segment)                                  > pivot
partial_URI = relative_part + maybe_str('?' + query)                    > pivot
origin_form = absolute_path + maybe_str('?' + query)                    > pivot
absolute_form = absolute_URI                                            > pivot
authority_form = authority                                              > pivot
asterisk_form = literal('*')                                            > auto
request_target = (origin_form |
                  absolute_form |
                  authority_form |
                  asterisk_form)                                        > pivot

reason_phrase = string(HTAB | SP | VCHAR | obs_text)                    > pivot

field_name = FieldName << token                                         > pivot

def transfer_parameter(no_q=False):
    return (
        (token__excluding(['q']) if no_q else token) *
        skip(BWS * '=' * BWS) * (token | quoted_string)
    ) > named(u'transfer-parameter', RFC(7230), is_pivot=True)

_built_in_codings = ['chunked', 'compress', 'deflate', 'gzip']
_empty_params = lambda c: Parametrized(c, MultiDict())

def transfer_extension(exclude=None, no_q=False):
    return Parametrized << (
        (TransferCoding << token__excluding(exclude or [])) *
        (MultiDict << many(skip(OWS * ';' * OWS) * transfer_parameter(no_q)))
    ) > named(u'transfer-extension', RFC(7230), is_pivot=True)

def transfer_coding(no_trailers=False, no_q=False):
    exclude = _built_in_codings
    if no_trailers:
        exclude = exclude + ['trailers']
    r = transfer_extension(exclude, no_q)
    for name in _built_in_codings:
        r = r | _empty_params << (TransferCoding << literal(name))
    return r > named(u'transfer-coding', RFC(7230), is_pivot=True)

Transfer_Encoding = comma_list1(transfer_coding())                      > pivot

rank = (float << '0' + maybe_str('.' + string_times(0, 3, DIGIT)) |
        float << '1' + maybe_str('.' + string_times(0, 3, '0')))        > pivot
t_ranking = skip(OWS * ';' * OWS * 'q=') * rank                         > pivot
t_codings = (CaseInsensitive << literal('trailers') |
             Parametrized << (transfer_coding(no_trailers=True, no_q=True) *
                              maybe(t_ranking)))                        > pivot
TE = comma_list(t_codings)                                              > pivot

Trailer = comma_list1(field_name)                                       > pivot

Host = uri_host + maybe_str(':' + port)                                 > pivot

connection_option = ConnectionOption << token                           > pivot
Connection = comma_list1(connection_option)                             > pivot

protocol_name = token                                                   > pivot
protocol_version = token                                                > pivot
protocol = Versioned << ((UpgradeToken << protocol_name) *
                         maybe(skip('/') * protocol_version))           > pivot
Upgrade = comma_list1(protocol)                                         > pivot

received_protocol = Versioned << (maybe(protocol_name * skip('/'), u'HTTP') *
                                  protocol_version)                     > pivot
pseudonym = token                                                       > pivot
received_by = uri_host + maybe_str(':' + port) | pseudonym              > pivot
Via = comma_list1(received_protocol * skip(RWS) *
                  received_by *
                  maybe(skip(RWS) * comment(include_parens=False)))     > pivot

Content_Length = int << string1(DIGIT)                                  > pivot

fill_names(globals(), RFC(7230))
