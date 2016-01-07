# -*- coding: utf-8; -*-

from httpolice.common import (
    AsteriskForm,
    OriginForm,
    Parameter,
    Parametrized,
)
from httpolice.header import FieldName, HeaderEntry
from httpolice.method import Method
from httpolice.parse import (
    argwrap,
    char_class,
    char_range,
    decode,
    decode_into,
    function,
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
    wrap,
)
from httpolice.transfer_coding import TransferCoding
from httpolice.version import HTTPVersion


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
token = string1(tchar)   // rfc(7230, u'token')
quoted_pair = (~literal('\\') + (char_class(HTAB + SP + VCHAR) | obs_text))
qdtext = char_class(HTAB + SP + '\x21' +
                    char_range(0x23, 0x5B) + char_range(0x5D, 0x7E)) | obs_text
quoted_string = (~dquote + string(qdtext | quoted_pair) + ~dquote) \
    // rfc(7230, u'quoted-string')
ctext = char_class(HTAB + SP + char_range(0x21, 0x27) +
                   char_range(0x2A, 0x5B) + char_range(0x5D, 0x7E)) | obs_text

def _parse_comment(state):            # recursive
    inner = decode(~literal('(') + string(ctext | quoted_pair | comment) +
                   ~literal(')'))   // rfc(7230, u'comment')
    return inner.parse(state)

comment = function(_parse_comment)

ows = string(sp_htab)
rws = string1(sp_htab)
bws = subst('', ows)

comma_list = lambda inner: maybe(empty=[], inner=argwrap(
    lambda x, xs: [elem for elem in [x] + xs if elem is not None],
    maybe(inner) + many(~(ows + ',') + maybe(~ows + inner))))
comma_list1 = lambda inner: argwrap(
    lambda x, xs: [elem for elem in [x] + xs if elem is not None],
    ~many(',' + ows) + inner +
    many(~(ows + ',') + maybe(~ows + inner)))

method = decode_into(Method, token)   // rfc(7230, u'method')

absolute_path = string1(join('/' + segment))   // rfc(7230, u'absolute-path')

origin_form = decode_into(
    OriginForm,
    join(absolute_path + maybe(join('?' + query), empty='')))
asterisk_form = decode_into(AsteriskForm, '*')

# FIXME: absolute-form, authority-form
request_target = origin_form | asterisk_form

http_version = decode_into(HTTPVersion, join('HTTP/' + digit + '.' + digit)) \
    // rfc(7230, u'HTTP-version')

request_line = (method + ~sp + request_target + ~sp + http_version + ~crlf)

field_name = decode_into(FieldName, token)   // rfc(7230, u'field-name')
field_vchar = char_class(VCHAR) | obs_text
field_content = wrap(str.rstrip,        # see errata to RFC 7230
                     join(field_vchar + string(sp_htab | field_vchar)))
obs_fold = subst(' ', ows + crlf + many1(sp_htab))
field_value = string(field_content | obs_fold)
header_field = argwrap(HeaderEntry,
                       field_name + ~(':' + ows) + field_value + ~ows)

transfer_parameter = argwrap(
    Parameter,
    decode(token) + ~(bws + '=' + bws) + decode(token | quoted_string)) \
    // rfc(7230, u'transfer-parameter')
transfer_extension = argwrap(
    Parametrized,
    decode_into(TransferCoding, token) +
    many(~(ows + ';' + ows) + transfer_parameter)) \
    // rfc(7230, u'transfer-extension')
# We don't special-case gzip/deflate/etc. here, as the ABNF doesn't preclude
# parsing "gzip" as <transfer-extension> with an empty list of parameters.
transfer_coding = transfer_extension

chunk_size = hex_integer   // rfc(7230, u'chunk-size')
chunk_ext_name = decode(token)   // rfc(7230, u'chunk-ext-name')
chunk_ext_val = decode(token | quoted_string)
chunk_ext = many(argwrap(
    Parameter,
    ~literal(';') + chunk_ext_name + maybe(~literal('=') + chunk_ext_val))) \
    // rfc(7230, u'chunk-ext')

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
