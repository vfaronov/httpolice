# -*- coding: utf-8; -*-

from httpolice.common import AsteriskForm, Comment, OriginForm
from httpolice.header import FieldName, HeaderEntry
from httpolice.method import Method
from httpolice.parse import (
    Parser,
    anything,
    char_class,
    char_range,
    decode_into,
    ignore,
    join,
    literal,
    many1,
    maybe,
    named,
    rfc,
    string,
    string1,
    wrap,
)
from httpolice.version import HTTPVersion


# RFC 5234

ALPHA = char_range(0x41, 0x5A) + char_range(0x61, 0x7A)
alpha = char_class(ALPHA)
crlf = named(u'newline', ignore(maybe(literal('\r'))) + literal('\n'))
DIGIT = char_range(0x30, 0x39)
digit = char_class(DIGIT)
HEXDIG = DIGIT + 'ABCDEFabcdef'
HTAB = '\t'
SP = ' '
sp = literal(SP)
sp_htab = char_class(SP + HTAB)
VCHAR = char_range(0x21, 0x7E)
DQUOTE = '"'
dquote = literal(DQUOTE)


# RFC 3986

pct_encoded = join(literal('%') + char_class(HEXDIG) + char_class(HEXDIG))
sub_delims = char_class("!$&'()*+,;=")
unreserved = char_class(ALPHA + DIGIT + "-._~")
pchar = unreserved | pct_encoded | sub_delims | char_class(':@')
segment = string(pchar)
query = string(pchar | char_class('/?'))


# RFC 7230

obs_text = char_class(char_range(0x80, 0xFF))

tchar = char_class("!#$%&'*+-.^_`|~" + DIGIT + ALPHA)
token = rfc(7230, 'token', string1(tchar))
quoted_pair = (ignore(literal('\\')) +
               (char_class(HTAB + SP + VCHAR) | obs_text))
qdtext = char_class(HTAB + SP + '\x21' +
                    char_range(0x23, 0x5B) + char_range(0x5D, 0x7E)) | obs_text
quoted_string = rfc(7230, 'quoted-string', (ignore(dquote) +
                                            string(qdtext | quoted_pair) +
                                            ignore(dquote)))
ctext = char_class(HTAB + SP + char_range(0x21, 0x27) +
                   char_range(0x2A, 0x5B) + char_range(0x5D, 0x7E)) | obs_text

class _CommentParser(Parser):             # recursive
    def parse(self, state):
        inner = rfc(7230, 'comment', decode_into(
            Comment,
            ignore(literal('(')) +
            string(ctext | quoted_pair | comment) +
            ignore(literal(')'))))
        return inner.parse(state)

comment = _CommentParser()

method = rfc(7230, 'method', decode_into(Method, token))

absolute_path = rfc(7230, 'absolute-path',
                    string1(join(literal('/') + segment)))

origin_form = decode_into(
    OriginForm,
    join(absolute_path + maybe(join(literal('?') + query))))
asterisk_form = decode_into(AsteriskForm, literal('*'))

# FIXME: absolute-form, authority-form
request_target = origin_form | asterisk_form

http_version = rfc(7230, 'HTTP-version', decode_into(
    HTTPVersion,
    join(literal('HTTP/') + digit + literal('.') + digit)))

request_line = (method + ignore(sp) + request_target + ignore(sp) +
                http_version + ignore(crlf))

ows = string(sp_htab)
rws = string1(sp_htab)
bws = wrap(lambda _: '', ows)

field_name = rfc(7230, 'field-name', decode_into(FieldName, token))
field_vchar = char_class(VCHAR) | obs_text
field_content = wrap(str.rstrip,        # see errata to RFC 7230
                     join(field_vchar + string(sp_htab | field_vchar)))
obs_fold = wrap(lambda _: ' ', ows + crlf + many1(sp_htab))
field_value = string(field_content | obs_fold)
header_field = wrap(lambda kv: HeaderEntry(*kv),
                    field_name + ignore(literal(':')) +
                    ignore(ows) + field_value + ignore(ows) + ignore(crlf))

comma_list = lambda _: wrap(lambda s: [s], anything())              # FIXME
comma_list1 = lambda _: wrap(lambda s: [s], anything())             # FIXME


# Auxiliary

integer = wrap(int, string1(digit))
