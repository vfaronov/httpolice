# -*- coding: utf-8; -*-

"""Access to the HTTPolice notices base.

Notices are written and stored in XML (``notices.xml``).
Before you scoff: XML is good for this purpose.
Firstly, the notices' explanations are free-form markup,
or *mixed content*--exactly what XML was designed for.
Secondly, lxml makes it easy to map XML elements to custom classes.
To render a notice, we recursively reduce these custom classes to strings,
obtaining an HTML tree (or plain text) along the way.

This module exposes the :data:`notices` variable,
which is a map from notice ID (:class:`int`) to :class:`Notice`.
"""

import copy
import pkgutil

import lxml.etree
import six

from httpolice import citation, known
from httpolice.util.ordered_enum import OrderedEnum


lookup = lxml.etree.ElementNamespaceClassLookup()
ns = lookup.get_namespace(None)


class Severity(OrderedEnum):

    """A notice's severity.

    This is a Python 3.4 style enumeration
    with the additional feature that its members are ordered:

    >>> Severity.comment < Severity.error
    True

    The underlying values of this enumeration are **not** part of the API.
    """

    error = 2
    comment = 1
    debug = 0


known_map = {name: cls for (cls, (_, name)) in known.classes.items()}


# pylint: disable=property-on-old-class


@ns('error')
@ns('comment')
@ns('debug')
class Notice(lxml.etree.ElementBase):

    """An element that represents a single notice, as template."""

    id = property(lambda self: int(self.get('id')))
    severity = property(lambda self: Severity[self.tag])
    severity_short = property(lambda self: self.severity.name[0].upper())
    title = property(lambda self: self.find('title').content)

    @property
    def explanation(self):
        for child in self:
            if isinstance(child, Title) or child.tag is lxml.etree.Comment:
                continue
            elif isinstance(child, (Paragraph, ExceptionDetails, Ref)):
                yield child
            else:
                # Assume that a wrapping ``<explain/>`` was omitted.
                para = _parser.makeelement('explain')
                para.append(copy.deepcopy(child))
                yield para


class Content(lxml.etree.ElementBase):

    """An element that has further content inside it."""

    @property
    def content(self):
        r = [self.text]
        for child in self:
            r.append(child)
            r.append(child.tail)
        r = [piece for piece in r if piece is not None and piece != u'']

        # Strip spaces from the first and last text children.
        # Useful for quotes.
        if r:
            if isinstance(r[0], (six.text_type, bytes)):
                r[0] = r[0].lstrip()
            if isinstance(r[-1], (six.text_type, bytes)):
                r[-1] = r[-1].rstrip()

        return r


@ns('explain')
class Paragraph(Content):

    """A paragraph of explanation."""

    pass


@ns('title')
class Title(Content):

    """A notice's title."""

    pass


@ns('ref')
class Ref(lxml.etree.ElementBase):

    """A reference to a piece of data, for highlights in HTML reports."""

    reference = property(lambda self: self.get('to').split('.'))


@ns('var')
class Var(Ref):

    """A placeholder for a piece of data from a notice's context.

    It also acts as an implicit :class:`Ref` to that data.
    """

    reference = property(lambda self: self.get('ref').split('.'))


@ns('exception')
class ExceptionDetails(lxml.etree.ElementBase):

    """A placeholder for details of the ``error`` key from the context."""

    pass


@ns('cite')
class Cite(Content):

    """A citation, with an optional quote."""

    @property
    def info(self):
        return citation.Citation(self.get('title'), self.get('url'))


@ns('rfc')
class CiteRFC(Cite):

    """A citation from an RFC, with an optional quote."""

    @property
    def info(self):
        return citation.RFC(self.get('num'),
                            self.get('sect'), self.get('appendix'),
                            self.get('errata'))


class Known(Content):

    """A protocol item known in advance, such as a header or a status code."""

    @property
    def content(self):
        [name] = super(Known, self).content
        return known_map[self.tag](name)


for tag in known_map:
    ns[tag] = Known


def _load_notices():
    parser = lxml.etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    notices_xml = pkgutil.get_data('httpolice', 'notices.xml')
    root = lxml.etree.fromstring(notices_xml, parser)
    r = {}
    for elem in root:
        if isinstance(elem, Notice):
            assert elem.id not in r
            r[elem.id] = elem
    return r, parser

(all_notices, _parser) = _load_notices()
