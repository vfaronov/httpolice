# -*- coding: utf-8; -*-

import six

from httpolice import known
from httpolice.header import HeaderView
from httpolice.parse import Symbol
from httpolice.structure import HeaderEntry, Parametrized
from httpolice.util.text import format_chars


def expand_piece(piece):
    if hasattr(piece, 'content'):
        return piece.content

    elif isinstance(piece, Symbol):
        return [piece.name, u' (', piece.citation, u')']

    elif isinstance(piece, Parametrized):
        return piece.item

    elif isinstance(piece, (HeaderEntry, HeaderView)):
        return piece.name

    else:
        return six.text_type(piece)


def expand_parse_error(error):
    paras = [[u'Parse error at byte offset %d.' % error.point]]
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
