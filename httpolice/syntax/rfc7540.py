# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import fill_names, pivot
from httpolice.syntax.rfc7235 import token68


HTTP2_Settings = token68                                                > pivot


fill_names(globals(), RFC(7540))
