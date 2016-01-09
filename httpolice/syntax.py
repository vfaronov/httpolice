# -*- coding: utf-8; -*-

import re

from httpolice.common import (
    AsteriskForm,
    ConnectionOption,
    FieldName,
    HeaderEntry,
    HTTPVersion,
    Method,
    OriginForm,
    Parametrized,
    StatusCode,
    TransferCoding,
)
from httpolice.parse import (
    ParseError,
    argwrap,
    char_class,
    char_range,
    ci,
    decode,
    decode_into,
    function,
    group,
    join,
    literal,
    many,
    many1,
    maybe,
    nbytes,
    rfc,
    string,
    string1,
    subst,
    times,
    wrap,
)


# RFC 5234

ALPHA = char_range(0x41, 0x5A) + char_range(0x61, 0x7A)
alpha = char_class(ALPHA)
crlf = (~maybe('\r') + '\n')   // u'newline'
DIGIT = char_range(0x30, 0x39)
digit = char_class(DIGIT)
HEXDIG = DIGIT + 'ABCDEFabcdef'
hexdig = char_class(HEXDIG)
HTAB = '\t'
SP = ' '
sp = literal(SP)
sp_htab = char_class(SP + HTAB)
VCHAR = char_range(0x21, 0x7E)
DQUOTE = '"'
dquote = literal(DQUOTE)


# Auxiliary

integer = wrap(int, string1(digit))
hex_integer = wrap(lambda s: int(s, 16), string1(hexdig))


# RFC 3986

pct_encoded = join('%' + char_class(HEXDIG) + char_class(HEXDIG))
sub_delims = char_class("!$&'()*+,;=")
unreserved = char_class(ALPHA + DIGIT + "-._~")
pchar = unreserved | pct_encoded | sub_delims | char_class(':@')
segment = string(pchar)
query = string(pchar | char_class('/?'))


# RFC 7230

obs_text = char_class(char_range(0x80, 0xFF))

tchar = char_class("!#$%&'*+-.^_`|~" + DIGIT + ALPHA)
token = decode(string1(tchar))   // rfc(7230, u'token')

def quoted_pair(sensible_for):
    # In RFC 7230 ``quoted-pair`` is a single rule,
    # but we parametrize it to report no. 1017 depending on the context.
    def parser(state):
        inner = (~literal('\\') + (char_class(HTAB + SP + VCHAR) | obs_text))
        r = inner.parse(state)
        if r not in sensible_for:
            state.complain(1017, char=r.decode('ascii', 'replace'))
        return r
    return function(parser)

qdtext = char_class(HTAB + SP + '\x21' +
                    char_range(0x23, 0x5B) + char_range(0x5D, 0x7E)) | obs_text
quoted_string = (~dquote + string(qdtext | quoted_pair('"\\')) + ~dquote) \
    // rfc(7230, u'quoted-string')
ctext = char_class(HTAB + SP + char_range(0x21, 0x27) +
                   char_range(0x2A, 0x5B) + char_range(0x5D, 0x7E)) | obs_text

def _parse_comment(state):            # recursive
    inner = decode(~literal('(') +
                    string(ctext | quoted_pair('()\\') | comment) +
                   ~literal(')'))   // rfc(7230, u'comment')
    return inner.parse(state)

comment = function(_parse_comment)

ows = string(sp_htab)

def _parse_rws(state):
    r = string1(sp_htab).parse(state)
    if r != ' ':
        state.complain(1014, num=len(r))
    return r
rws = function(_parse_rws)

def _parse_bws(state):
    r = ows.parse(state)
    if r:
        state.complain(1015)
    return ''
bws = function(_parse_bws)

comma_list = lambda inner: maybe(empty=[], inner=argwrap(
    lambda x, xs: [elem for elem in [x] + xs if elem is not None],
    maybe(inner) + many(~(ows + ',') + maybe(~ows + inner))))
comma_list1 = lambda inner: argwrap(
    lambda x, xs: [elem for elem in [x] + xs if elem is not None],
    ~many(',' + ows) + inner +
    many(~(ows + ',') + maybe(~ows + inner)))

method = wrap(Method, token)   // rfc(7230, u'method')

absolute_path = string1(join('/' + segment))   // rfc(7230, u'absolute-path')

origin_form = decode_into(
    OriginForm,
    join(absolute_path + maybe(join('?' + query), empty='')))
asterisk_form = decode_into(AsteriskForm, '*')

# FIXME: absolute-form, authority-form
request_target = origin_form | asterisk_form

http_version = decode_into(HTTPVersion, join('HTTP/' + digit + '.' + digit)) \
    // rfc(7230, u'HTTP-version')

status_code = wrap(StatusCode, join(times(3, 3, digit))) \
    // rfc(7230, u'status-code')
reason_phrase = string(char_class(HTAB + SP + VCHAR) | obs_text) \
    // rfc(7230, u'reason-phrase')

request_line = method + ~sp + request_target + ~sp + http_version + ~crlf
status_line = http_version + ~sp + status_code + ~sp + reason_phrase + ~crlf

field_name = wrap(FieldName, token)   // rfc(7230, u'field-name')
field_vchar = char_class(VCHAR) | obs_text
field_content = wrap(str.rstrip,        # see errata to RFC 7230
                     join(field_vchar + string(sp_htab | field_vchar)))

def _parse_obs_fold(state):
    (ows + crlf + many1(sp_htab)).parse(state)
    state.complain(1016)
    return ' '
obs_fold = function(_parse_obs_fold)

field_value = string(field_content | obs_fold)
header_field = argwrap(HeaderEntry,
                       field_name + ~(':' + ows) + field_value + ~ows)

transfer_parameter = \
    (token + ~(bws + '=' + bws) + (token | decode(quoted_string))) \
    // rfc(7230, u'transfer-parameter')
transfer_extension = argwrap(
    Parametrized,
    wrap(TransferCoding, token) +
    many(~(ows + ';' + ows) + transfer_parameter)) \
    // rfc(7230, u'transfer-extension')
# We don't special-case gzip/deflate/etc. here, as the ABNF doesn't preclude
# parsing "gzip" as <transfer-extension> with an empty list of parameters.
transfer_coding = transfer_extension

def _check_rank(coding):
    # The <t-ranking> is parsed as part of the <transfer-extension>,
    # so we need to check it manually.
    if coding.param:
        name, value = coding.param.pop()
        if name.lower() == u'q':
            if not re.match(ur'0(\.[0-9]{0,3})?', value) and \
                    not re.match(ur'1(\.0{0,3})?', value):
                raise ParseError(u'bad <rank> (RFC 7230): %r' % value)
            value = float(value)
        coding.param.append((name, value))
    return coding

t_codings = (ci('trailers') | wrap(_check_rank, transfer_coding))

chunk_size = hex_integer   // rfc(7230, u'chunk-size')
chunk_ext_name = token   // rfc(7230, u'chunk-ext-name')
chunk_ext_val = token | decode(quoted_string)
chunk_ext = \
    many(~literal(';') + chunk_ext_name +
          maybe(~literal('=') + chunk_ext_val))   // rfc(7230, u'chunk-ext')

def _parse_chunk(state):
    size = chunk_size.parse(state)
    maybe(chunk_ext).parse(state)
    crlf.parse(state)
    if size == 0:
        return ''
    else:
        data = nbytes(size, size).parse(state)
        crlf.parse(state)
        return data

chunk = function(_parse_chunk)
trailer_part = many(header_field + ~crlf)

connection_option = wrap(ConnectionOption, token)


# RFC 7231

product_version = token
product = group(token + maybe(~literal('/') + product_version))
user_agent = argwrap(
    lambda p1, ps: [p1] + ps,
    product + many(~rws + many(product | comment)))
