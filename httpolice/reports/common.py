# -*- coding: utf-8; -*-

from singledispatch import singledispatch
import six

from httpolice import known, notice
from httpolice.header import HeaderView
from httpolice.known import h
from httpolice.parse import ParseError, Symbol
from httpolice.structure import FieldName, HeaderEntry, Parametrized
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
    return expand_piece(hdr.name)

@expand_piece.register(FieldName)
def expand_field_name(name):
    # Canonicalize field names. For example, if the header is called
    # "cache-control" in the message (as it always is in HTTP/2),
    # it should be rendered as "Cache-Control" in the report.
    if name in h:
        return h[name]['_']
    else:
        return name


@singledispatch
def expand_error(error):
    return [error]      # A single paragraph consisting of the error message.

@expand_error.register(ParseError)
def expand_parse_error(error):
    paras = [[error.name]] if error.name else []
    paras.append([u'Parse error at offset %d.' % error.point])
    if error.found == b'':
        paras.append([u'Found end of data.'])
    elif error.found is not None:
        paras.append([u'Found: %s' % format_chars([error.found])])

    for i, (option, as_part_of) in enumerate(error.expected):
        if i == 0:
            paras.append([u'Expected:'])
            para = [option]
        else:
            para = [u'or ', option]
        if as_part_of:
            para.append(u' as part of ')
            for j, parent in enumerate(as_part_of):
                para.extend([u' or ', parent] if j > 0 else [parent])
        paras.append(para)

    return paras


def find_reason_phrase(response):
    return response.reason or known.title(response.status) or u'(unknown)'
