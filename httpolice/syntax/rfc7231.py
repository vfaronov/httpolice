# -*- coding: utf-8; -*-

from httpolice.common import (
    CaseInsensitive,
    ContentCoding,
    MediaType,
    Parametrized,
    Product,
)
from httpolice.parse import (
    argwrap,
    decode,
    join,
    literal,
    many,
    maybe,
    rfc,
    wrap,
)
from httpolice.syntax.rfc7230 import comment, ows, quoted_string, rws, token


parameter = (wrap(CaseInsensitive, token) + ~literal('=') +
             (token | decode(quoted_string)))   // rfc(7231, u'parameter')
type_ = token
subtype = token
media_type = argwrap(
    Parametrized,
    wrap(MediaType, join(type_ + '/' + subtype)) +
    many(~(ows + ';' + ows) + parameter))    // rfc(7231, u'media-type')

content_coding = wrap(ContentCoding, token)    // rfc(7231, u'content-coding')

product_version = token
product = argwrap(Product, token + maybe(~literal('/') + product_version))
user_agent = argwrap(
    lambda p1, ps: [p1] + ps,
    product + many(~rws + (product | comment)))
