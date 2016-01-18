# -*- coding: utf-8; -*-

from httpolice.common import LanguageTag
from httpolice.parse import wrap
from httpolice.syntax.rfc5646 import language_tag


language_range = language_tag | wrap(LanguageTag, '*')
