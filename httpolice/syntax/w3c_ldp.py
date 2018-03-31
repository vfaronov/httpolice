# -*- coding: utf-8; -*-

from httpolice.citation import Citation
from httpolice.parse import fill_names, pivot
from httpolice.syntax.rfc7230 import comma_list
from httpolice.syntax.rfc7231 import media_range


Accept_Post = comma_list(media_range())                                > pivot

fill_names(globals(), Citation(u'W3C Linked Data Platform 1.0',
                               u'https://www.w3.org/TR/ldp/'))
