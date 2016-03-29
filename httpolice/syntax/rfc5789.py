# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import fill_names, pivot
from httpolice.syntax.rfc7230 import comma_list1
from httpolice.syntax.rfc7231 import media_type


Accept_Patch = comma_list1(media_type)                                  > pivot

fill_names(globals(), RFC(5789))
