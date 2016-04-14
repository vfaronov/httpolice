# -*- coding: utf-8; -*-

from httpolice.reports.html import html_report
from httpolice.reports.text import text_report


formats = {
    u'text': text_report,
    u'html': html_report,
}
