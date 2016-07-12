# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import (fill_names, literal, mark, maybe, maybe_str,
                             named, pivot, skip, string1, string_times)
from httpolice.structure import (CacheDirective, CaseInsensitive, Parametrized,
                                 WarnCode, WarningValue)
from httpolice.syntax.common import DIGIT, DQUOTE, SP
from httpolice.syntax.rfc7230 import (comma_list1, port, pseudonym,
                                      quoted_string, token, token__excluding,
                                      uri_host)
from httpolice.syntax.rfc7231 import HTTP_date


delta_seconds = int << string1(DIGIT)                                   > pivot
Age = delta_seconds                                                     > pivot

cache_directive = Parametrized << (
    (CacheDirective << token) *
    maybe(skip('=') * (mark(token) | mark(quoted_string))))             > pivot
Cache_Control = comma_list1(cache_directive)                            > pivot

Expires = HTTP_date                                                     > pivot

def extension_pragma(exclude_no_cache=False):
    return Parametrized << (
        (token__excluding(['no-cache']) if exclude_no_cache else token) *
        maybe(skip('=') * (token | quoted_string))
    ) > named(u'extension-pragma', RFC(7234), is_pivot=True)

pragma_directive = (CaseInsensitive << literal('no-cache') |
                    extension_pragma(exclude_no_cache=True))            > pivot
Pragma = comma_list1(pragma_directive)                                  > pivot

warn_code = WarnCode << string_times(3, 3, DIGIT)                       > pivot
warn_agent = uri_host + maybe_str(':' + port) | pseudonym               > pivot
warn_text = quoted_string                                               > pivot
warn_date = skip(DQUOTE) * HTTP_date * skip(DQUOTE)                     > pivot
warning_value = WarningValue << (warn_code * skip(SP) *
                                 warn_agent * skip(SP) *
                                 warn_text *
                                 maybe(skip(SP) * warn_date))           > pivot
Warning_ = comma_list1(warning_value)                                   > pivot

fill_names(globals(), RFC(7234))
