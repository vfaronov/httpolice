# -*- coding: utf-8; -*-

import lxml.etree
import pkg_resources

from httpolice import citation, structure


protocol_items = {
    'auth': structure.AuthScheme,
    'cache': structure.CacheDirective,
    'cc': structure.ContentCoding,
    'h': structure.FieldName,
    'm': structure.Method,
    'media': structure.MediaType,
    'st': structure.StatusCode,
    'tc': structure.TransferCoding,
    'warn': structure.WarnCode,
}


class Notice(lxml.etree.ElementBase):

    ident = property(lambda self: int(self.get('id')))
    severity = property(lambda self: self.tag)
    severity_short = property(lambda self: self.tag[0].upper())
    title = property(lambda self: self.find('title').contents)
    explanation = property(lambda self: [
        [child] if child.tag == 'rfc' else child.contents
        for child in self
        if child.tag != 'title' and child.tag is not lxml.etree.Comment])


class Text(lxml.etree.ElementBase):

    @property
    def contents(self):
        r = [self.text]
        for child in self:
            r.append(child)
            r.append(child.tail)
        return [piece for piece in r if piece not in [None, u'']]


class Ref(Text):

    get_contents = lambda self, ctx: self.contents or [self.resolve(ctx)]

    def resolve(self, ctx):
        path = self.get('to').split('.')
        node = ctx[path.pop(0)]
        for attr_name in path:
            node = getattr(node, attr_name)
        return node


class Citation(Text):

    @property
    def info(self):
        return citation.Citation(self.get('title'), self.get('url'))


class RFC(Citation):

    @property
    def info(self):
        num = int(self.get('num'))
        if self.get('sect'):
            sect = tuple(int(n) for n in self.get('sect').split('.'))
        else:
            sect = None
        return citation.RFC(num, section=sect)


class ProtocolItem(lxml.etree.ElementBase):

    contents = property(lambda self: [protocol_items[self.tag](self.text)])


def load_notices():
    lookup = lxml.etree.ElementNamespaceClassLookup()
    parser = lxml.etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    ns = lookup.get_namespace(None)
    for tag in ['error', 'comment', 'debug']:
        ns[tag] = Notice
    ns['title'] = ns['explain'] = Text
    ns['ref'] = Ref
    ns['cite'] = Citation
    ns['rfc'] = RFC
    for tag in protocol_items:
        ns[tag] = ProtocolItem
    notices_xml = pkg_resources.resource_stream('httpolice', 'notices.xml')
    tree = lxml.etree.parse(notices_xml, parser)
    r = {}
    for elem in tree.getroot():
        if isinstance(elem, Notice):
            assert elem.ident not in r
            r[elem.ident] = elem
    return r

notices = load_notices()
