# -*- coding: utf-8; -*-

from httpolice.common import EntityTag
from httpolice.parse import (
    argwrap,
    char_class,
    char_range,
    function,
    literal,
    maybe,
    string,
    subst,
)
from httpolice.syntax.common import dquote
from httpolice.syntax.rfc7230 import obs_text


weak = subst(True, literal('W/'))
etagc = char_class('\x21' + char_range(0x23, 0x7E)) | obs_text

def _parse_opaque_tag(state):
    r = (~dquote + string(etagc) + ~dquote).parse(state)
    if '\\' in r:
        state.complain(1119)
    return r

opaque_tag = function(_parse_opaque_tag)
entity_tag = argwrap(EntityTag, maybe(weak, False) + opaque_tag)
