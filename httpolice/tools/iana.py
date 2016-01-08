# -*- coding: utf-8; -*-

import re
import urllib2
import urlparse

import lxml.etree

from httpolice import header, method, status_code, transfer_coding
from httpolice.common import Citation, RFC


def yes_no(s):
    return {'yes': True, 'no': False}[s]


class Registry(object):

    key_order = []
    xmlns = {'iana': 'http://www.iana.org/assignments'}

    def __init__(self, base_url='http://www.iana.org/assignments/'):
        self.base_url = base_url

    def _get_xml(self, relative_url):
        req = urllib2.Request(
            urlparse.urljoin(self.base_url, relative_url),
            headers={'Accept': 'text/xml, application/xml',
                     'User-Agent': 'HTTPolice-IANA-tool Python-urllib'})
        return lxml.etree.parse(urllib2.urlopen(req))

    def extract_citations(self, record):
        for xref in record.findall('iana:xref', self.xmlns):
            if xref.get('type') == 'rfc':
                match = re.match(
                    r'RFC(\d+), (Section|Appendix) ([A-Z0-9]+(\.[0-9]+)*)',
                    xref.text or '')
                if match:
                    num = int(match.group(1))
                    kw = match.group(2).lower()
                    sect = tuple(int(n) if n.isdigit() else n
                                 for n in match.group(3).split('.'))
                    yield RFC(num, **{kw: sect})
                else:
                    num = int(xref.get('data')[3:])
                    yield RFC(num)
            elif xref.get('type') == 'uri':
                yield Citation(xref.text, xref.get('data'))


class HeaderRegistry(Registry):

    def get_all(self):
        tree = self._get_xml('message-headers/message-headers.xml')
        entries = []
        for record in tree.findall('//iana:record', self.xmlns):
            if record.find('iana:protocol', self.xmlns).text != 'http':
                continue
            value = record.find('iana:value', self.xmlns)
            entry = {
                '_': header.FieldName(value.text),
                '_citations': list(self.extract_citations(record)),
            }
            entries.append(entry)
            status = record.find('iana:status', self.xmlns)
            if (status is not None) and status.text:
                entry['iana_status'] = status.text
        return [('headers', entries, header.known_headers)]


class MethodRegistry(Registry):

    def get_all(self):
        tree = self._get_xml('http-methods/http-methods.xml')
        entries = []
        for record in tree.findall('//iana:record', self.xmlns):
            entries.append({
                '_': method.Method(record.find('iana:value', self.xmlns).text),
                '_citations': list(self.extract_citations(record)),
                'safe': yes_no(record.find('iana:safe', self.xmlns).text),
                'idempotent':
                    yes_no(record.find('iana:idempotent', self.xmlns).text),
            })
        return [('methods', entries, method.known_methods)]


class StatusCodeRegistry(Registry):

    def get_all(self):
        tree = self._get_xml('http-status-codes/http-status-codes.xml')
        entries = []
        for record in tree.findall('//iana:record', self.xmlns):
            value = record.find('iana:value', self.xmlns).text
            if not value.isdigit():
                continue
            description = record.find('iana:description', self.xmlns).text
            if description.lower() == 'unassigned':
                continue
            entries.append({
                '_': status_code.StatusCode(value),
                '_citations': list(self.extract_citations(record)),
                'description': description,
            })
        return [('status codes', entries, status_code.known_codes)]


class ParametersRegistry(Registry):

    def get_all(self):
        tree = self._get_xml('http-parameters/http-parameters.xml')
        return [
            ('transfer codings',
             list(self._transfer_codings(tree)),
             transfer_coding.known_codings),
        ]

    def _transfer_codings(self, tree):
        records = tree.findall(
            '//iana:registry[@id="transfer-coding"]/iana:record', self.xmlns)
        for record in records:
            yield {
                '_': transfer_coding.TransferCoding(
                    record.find('iana:name', self.xmlns).text),
                '_citations': list(self.extract_citations(record)),
            }
