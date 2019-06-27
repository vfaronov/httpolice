from httpolice.citation import Citation
from httpolice.parse import (auto, case_sens, fill_names, literal, maybe_str,
                             pivot)
from httpolice.syntax.rfc3986 import host, port, scheme
from httpolice.syntax.rfc7230 import (comma_list, comma_list1, field_name,
                                      method)
from httpolice.syntax.rfc7234 import delta_seconds


# WHATWG actually uses their own definitions for scheme, host, and port,
# but that's a bit too far for HTTPolice, we can live with RFC 3986.
origin = scheme + '://' + host + maybe_str(':' + port)                  > pivot
origin_or_null = origin | case_sens('null')                             > pivot
Origin = origin_or_null                                                 > pivot

Access_Control_Request_Method = method                                  > pivot
Access_Control_Request_Headers = comma_list1(field_name)                > pivot
wildcard = literal('*')                                                 > auto
Access_Control_Allow_Origin = origin_or_null | wildcard                 > pivot
Access_Control_Allow_Credentials = case_sens('true')                    > pivot
Access_Control_Expose_Headers = comma_list(field_name)                  > pivot
Access_Control_Max_Age = delta_seconds                                  > pivot
Access_Control_Allow_Methods = comma_list(method)                       > pivot
Access_Control_Allow_Headers = comma_list(field_name)                   > pivot

X_Content_Type_Options = literal('nosniff')                             > pivot

Cross_Origin_Resource_Policy = (
    case_sens('same-origin') | case_sens('same-site'))                  > pivot

fill_names(globals(), Citation(u'WHATWG Fetch',
                               u'https://fetch.spec.whatwg.org/'))
