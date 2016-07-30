# -*- coding: utf-8; -*-

from httpolice import helpers
from httpolice.__metadata__ import version as __version__
from httpolice.blackboard import Complaint
from httpolice.exchange import Exchange, check_exchange
from httpolice.notice import Severity
from httpolice.reports.html import html_report
from httpolice.reports.text import text_report
from httpolice.request import Request
from httpolice.response import Response

# Backward compatibility
ERROR = Severity.error
COMMENT = Severity.comment
DEBUG = Severity.debug

__all__ = [
    'Complaint',
    'Exchange',
    'Request',
    'Response',
    'Severity',
    'COMMENT',
    'DEBUG',
    'ERROR',
    'check_exchange',
    'helpers',
    'html_report',
    'text_report',
]
