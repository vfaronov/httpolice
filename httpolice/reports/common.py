# -*- coding: utf-8; -*-

from singledispatch import singledispatch
import six

from httpolice import known, notice
from httpolice.header import HeaderView
from httpolice.parse import ParseError, Symbol
from httpolice.structure import HeaderEntry, Parametrized
from httpolice.util.text import format_chars


def resolve_reference(ctx, path):
    path = list(path)
    node = ctx[path.pop(0)]
    for attr_name in path:
        node = getattr(node, attr_name)
    return node


@singledispatch
def expand_piece(piece):
    return six.text_type(piece)

@expand_piece.register(notice.Content)
def expand_elem(elem):
    return elem.content

@expand_piece.register(Symbol)
def expand_symbol(sym):
    if sym.citation:
        return [sym.name, u' (', sym.citation, u')']
    else:
        return [sym.name]

@expand_piece.register(Parametrized)
def expand_parametrized(x):
    return x.item

@expand_piece.register(HeaderEntry)
@expand_piece.register(HeaderView)
def expand_header(hdr):
    # Canonicalize field names. For example, if the header is called
    # "cache-control" in the message (as it always is in HTTP/2),
    # it should be rendered as "Cache-Control" in the report.
    # Note that we only do this when expanding `HeaderEntry` and `HeaderView`,
    # not `FieldName`. This is because the latter is rendered in message
    # previews in HTML reports, where we don't want to change the original
    # casing.
    return known.header.get(hdr.name).get('key', hdr.name)


@singledispatch
def expand_error(error):
    return [error]      # A single paragraph consisting of the error message.

@expand_error.register(ParseError)
def expand_parse_error(error):
    paras = [[error.name]] if error.name else []
    paras.append([u'Parse error at offset %d.' % error.position])
    if error.found == b'':
        paras.append([u'Found end of data.'])
    elif error.found is not None:
        paras.append([u'Found: %s' % format_chars([error.found])])

    paras.append([u'Expected:'])
    for i, (option, symbols) in enumerate(error.expected):
        para = []
        if option:
            para.extend([option] if i == 0 else [u'or ', option])
            if symbols:
                para.append(u' as part of ')
        for j, symbol in enumerate(symbols or []):
            para.extend([symbol] if j == 0 else [u' or ', symbol])
        paras.append(para)

    return paras


def find_reason_phrase(response):
    return response.reason or known.title(response.status) or u'(unknown)'
