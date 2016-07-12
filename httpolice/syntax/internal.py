# -*- coding: utf-8; -*-

from httpolice.parse import (fill_names, literal, maybe, pivot, skip, string1,
                             subst)
from httpolice.syntax.common import DIGIT
from httpolice.syntax.rfc7230 import RWS, comma_list


notice_id = int << string1(DIGIT)                                       > pivot
resp = subst(True) << literal('resp')                                   > pivot
HTTPolice_Silence = comma_list(notice_id * maybe(skip(RWS) * resp))     > pivot


fill_names(globals(), citation=None)
