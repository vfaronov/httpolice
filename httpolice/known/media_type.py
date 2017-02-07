# -*- coding: utf-8; -*-

from httpolice.citation import RFC, Citation
from httpolice.known.base import KnownDict
from httpolice.structure import MediaType


def deprecated(name):
    return known.get_info(name).get('deprecated')

def is_json(name):
    return known.get_info(name).get('is_json') or name.endswith(u'+json')

def is_xml(name):
    return known.get_info(name).get('is_xml') or name.endswith(u'+xml')

def is_multipart(name):
    return name.startswith(u'multipart/')

def is_patch(name):
    return known.get_info(name).get('patch')


# When adding a new media type, fill in the fields as follows:
#
#   ``_``, ``_citations``
#     Obvious, and usually filled by ``tools/iana.py``.
#
#   ``patch``
#     Whether this media type is a patch, usable with the PATCH method
#     (see RFC 5789 errata).
#
#   ``is_json``
#     Set this to ``True`` if the media type uses JSON syntax
#     but **does not end** with ``+json``.
#
#   ``is_xml``
#     Set this to ``True`` if the media type uses XML syntax
#     but **does not end** with ``+xml``.
#
#   ``deprecated``
#     Filled by ``tools/iana.py``. You should not need to change it.

known = KnownDict(MediaType, [
 {'_': MediaType(u'application/1d-interleaved-parityfec'),
  '_citations': [RFC(6015)]},
 {'_': MediaType(u'application/alto-costmap+json'), '_citations': [RFC(7285)]},
 {'_': MediaType(u'application/alto-costmapfilter+json'),
  '_citations': [RFC(7285)]},
 {'_': MediaType(u'application/alto-directory+json'),
  '_citations': [RFC(7285)]},
 {'_': MediaType(u'application/alto-endpointprop+json'),
  '_citations': [RFC(7285)]},
 {'_': MediaType(u'application/alto-endpointpropparams+json'),
  '_citations': [RFC(7285)]},
 {'_': MediaType(u'application/alto-endpointcost+json'),
  '_citations': [RFC(7285)]},
 {'_': MediaType(u'application/alto-endpointcostparams+json'),
  '_citations': [RFC(7285)]},
 {'_': MediaType(u'application/alto-error+json'), '_citations': [RFC(7285)]},
 {'_': MediaType(u'application/alto-networkmapfilter+json'),
  '_citations': [RFC(7285)]},
 {'_': MediaType(u'application/alto-networkmap+json'),
  '_citations': [RFC(7285)]},
 {'_': MediaType(u'application/atom+xml'),
  '_citations': [RFC(4287), RFC(5023)]},
 {'_': MediaType(u'application/atomcat+xml'), '_citations': [RFC(5023)]},
 {'_': MediaType(u'application/atomdeleted+xml'), '_citations': [RFC(6721)]},
 {'_': MediaType(u'application/atomsvc+xml'), '_citations': [RFC(5023)]},
 {'_': MediaType(u'application/auth-policy+xml'), '_citations': [RFC(4745)]},
 {'_': MediaType(u'application/batch-smtp'), '_citations': [RFC(2442)]},
 {'_': MediaType(u'application/beep+xml'), '_citations': [RFC(3080)]},
 {'_': MediaType(u'application/calendar+json'), '_citations': [RFC(7265)]},
 {'_': MediaType(u'application/calendar+xml'), '_citations': [RFC(6321)]},
 {'_': MediaType(u'application/call-completion'), '_citations': [RFC(6910)]},
 {'_': MediaType(u'application/cals-1840'), '_citations': [RFC(1895)]},
 {'_': MediaType(u'application/cbor'), '_citations': [RFC(7049)]},
 {'_': MediaType(u'application/ccmp+xml'), '_citations': [RFC(6503)]},
 {'_': MediaType(u'application/ccxml+xml'), '_citations': [RFC(4267)]},
 {'_': MediaType(u'application/cdmi-capability'), '_citations': [RFC(6208)]},
 {'_': MediaType(u'application/cdmi-container'), '_citations': [RFC(6208)]},
 {'_': MediaType(u'application/cdmi-domain'), '_citations': [RFC(6208)]},
 {'_': MediaType(u'application/cdmi-object'), '_citations': [RFC(6208)]},
 {'_': MediaType(u'application/cdmi-queue'), '_citations': [RFC(6208)]},
 {'_': MediaType(u'application/cdni'), '_citations': [RFC(7736)]},
 {'_': MediaType(u'application/cellml+xml'), '_citations': [RFC(4708)]},
 {'_': MediaType(u'application/cfw'), '_citations': [RFC(6230)]},
 {'_': MediaType(u'application/cms'), '_citations': [RFC(7193)]},
 {'_': MediaType(u'application/cnrp+xml'), '_citations': [RFC(3367)]},
 {'_': MediaType(u'application/coap-group+json'), '_citations': [RFC(7390)]},
 {'_': MediaType(u'application/conference-info+xml'),
  '_citations': [RFC(4575)]},
 {'_': MediaType(u'application/cpl+xml'), '_citations': [RFC(3880)]},
 {'_': MediaType(u'application/csrattrs'), '_citations': [RFC(7030)]},
 {'_': MediaType(u'application/davmount+xml'), '_citations': [RFC(4709)]},
 {'_': MediaType(u'application/dialog-info+xml'), '_citations': [RFC(4235)]},
 {'_': MediaType(u'application/dicom'), '_citations': [RFC(3240)]},
 {'_': MediaType(u'application/dns'), '_citations': [RFC(4027)]},
 {'_': MediaType(u'application/dskpp+xml'), '_citations': [RFC(6063)]},
 {'_': MediaType(u'application/dssc+der'), '_citations': [RFC(5698)]},
 {'_': MediaType(u'application/dssc+xml'), '_citations': [RFC(5698)]},
 {'_': MediaType(u'application/dvcs'), '_citations': [RFC(3029)]},
 {'_': MediaType(u'application/ecmascript'), '_citations': [RFC(4329)]},
 {'_': MediaType(u'application/edi-consent'), '_citations': [RFC(1767)]},
 {'_': MediaType(u'application/edifact'), '_citations': [RFC(1767)]},
 {'_': MediaType(u'application/edi-x12'), '_citations': [RFC(1767)]},
 {'_': MediaType(u'application/emergencycalldata.comment+xml'),
  '_citations': [RFC(7852)]},
 {'_': MediaType(u'application/emergencycalldata.providerinfo+xml'),
  '_citations': [RFC(7852)]},
 {'_': MediaType(u'application/emergencycalldata.serviceinfo+xml'),
  '_citations': [RFC(7852)]},
 {'_': MediaType(u'application/emergencycalldata.deviceinfo+xml'),
  '_citations': [RFC(7852)]},
 {'_': MediaType(u'application/emergencycalldata.subscriberinfo+xml'),
  '_citations': [RFC(7852)]},
 {'_': MediaType(u'application/emma+xml'),
  '_citations': [Citation(None,
                          u'http://www.w3.org/TR/2007/CR-emma-20071211/'
                          u'#media-type-registration')]},
 {'_': MediaType(u'application/encaprtp'), '_citations': [RFC(6849)]},
 {'_': MediaType(u'application/epp+xml'), '_citations': [RFC(5730)]},
 {'_': MediaType(u'application/example'), '_citations': [RFC(4735)]},
 {'_': MediaType(u'application/exi'),
  '_citations': [Citation(None,
                          u'http://www.w3.org/TR/2009/'
                          u'CR-exi-20091208/#mediaTypeRegistration')]},
 {'_': MediaType(u'application/fdt+xml'), '_citations': [RFC(6726)]},
 {'_': MediaType(u'application/fits'), '_citations': [RFC(4047)]},
 {'_': MediaType(u'application/font-tdpfr'), '_citations': [RFC(3073)]},
 {'_': MediaType(u'application/framework-attributes+xml'),
  '_citations': [RFC(6230)]},
 {'_': MediaType(u'application/geo+json'), '_citations': [RFC(7946)]},
 {'_': MediaType(u'application/gzip'), '_citations': [RFC(6713)]},
 {'_': MediaType(u'application/h224'), '_citations': [RFC(4573)]},
 {'_': MediaType(u'application/held+xml'), '_citations': [RFC(5985)]},
 {'_': MediaType(u'application/http'), '_citations': [RFC(7230)]},
 {'_': MediaType(u'application/ibe-key-request+xml'),
  '_citations': [RFC(5408)]},
 {'_': MediaType(u'application/ibe-pkg-reply+xml'), '_citations': [RFC(5408)]},
 {'_': MediaType(u'application/ibe-pp-data'), '_citations': [RFC(5408)]},
 {'_': MediaType(u'application/im-iscomposing+xml'),
  '_citations': [RFC(3994)]},
 {'_': MediaType(u'application/index'), '_citations': [RFC(2652)]},
 {'_': MediaType(u'application/index.cmd'), '_citations': [RFC(2652)]},
 {'_': MediaType(u'application/index.obj'), '_citations': [RFC(2652)]},
 {'_': MediaType(u'application/index.response'), '_citations': [RFC(2652)]},
 {'_': MediaType(u'application/index.vnd'), '_citations': [RFC(2652)]},
 {'_': MediaType(u'application/iotp'), '_citations': [RFC(2935)]},
 {'_': MediaType(u'application/ipfix'), '_citations': [RFC(5655)]},
 {'_': MediaType(u'application/ipp'), '_citations': [RFC(2910)]},
 {'_': MediaType(u'application/isup'), '_citations': [RFC(3204)]},
 {'_': MediaType(u'application/javascript'), '_citations': [RFC(4329)]},
 {'_': MediaType(u'application/jose'), '_citations': [RFC(7515)]},
 {'_': MediaType(u'application/jose+json'), '_citations': [RFC(7515)]},
 {'_': MediaType(u'application/jrd+json'), '_citations': [RFC(7033)]},
 {'_': MediaType(u'application/json'),
  '_citations': [RFC(7159)],
  'is_json': True,
  'patch': False},
 {'_': MediaType(u'application/json-patch+json'), '_citations': [RFC(6902)],
  'patch': True},
 {'_': MediaType(u'application/json-seq'), '_citations': [RFC(7464)]},
 {'_': MediaType(u'application/jwk+json'), '_citations': [RFC(7517)]},
 {'_': MediaType(u'application/jwk-set+json'), '_citations': [RFC(7517)]},
 {'_': MediaType(u'application/jwt'), '_citations': [RFC(7519)]},
 {'_': MediaType(u'application/kpml-request+xml'), '_citations': [RFC(4730)]},
 {'_': MediaType(u'application/kpml-response+xml'), '_citations': [RFC(4730)]},
 {'_': MediaType(u'application/lgr+xml'), '_citations': [RFC(7940)]},
 {'_': MediaType(u'application/link-format'), '_citations': [RFC(6690)]},
 {'_': MediaType(u'application/load-control+xml'), '_citations': [RFC(7200)]},
 {'_': MediaType(u'application/lost+xml'), '_citations': [RFC(5222)]},
 {'_': MediaType(u'application/lostsync+xml'), '_citations': [RFC(6739)]},
 {'_': MediaType(u'application/mads+xml'), '_citations': [RFC(6207)]},
 {'_': MediaType(u'application/marc'), '_citations': [RFC(2220)]},
 {'_': MediaType(u'application/marcxml+xml'), '_citations': [RFC(6207)]},
 {'_': MediaType(u'application/mathml-content+xml'),
  '_citations': [Citation(None,
                          'http://www.w3.org/TR/MathML3/appendixb.html')]},
 {'_': MediaType(u'application/mathml-presentation+xml'),
  '_citations': [Citation(None,
                          'http://www.w3.org/TR/MathML3/appendixb.html')]},
 {'_': MediaType(u'application/mathml+xml'),
  '_citations': [Citation(None,
                          'http://www.w3.org/TR/MathML3/appendixb.html')]},
 {'_': MediaType(u'application/mbox'), '_citations': [RFC(4155)]},
 {'_': MediaType(u'application/media_control+xml'), '_citations': [RFC(5168)]},
 {'_': MediaType(u'application/media-policy-dataset+xml'),
  '_citations': [RFC(6796)]},
 {'_': MediaType(u'application/mediaservercontrol+xml'),
  '_citations': [RFC(5022)]},
 {'_': MediaType(u'application/merge-patch+json'), '_citations': [RFC(7396)],
  'patch': True},
 {'_': MediaType(u'application/metalink4+xml'), '_citations': [RFC(5854)]},
 {'_': MediaType(u'application/mets+xml'), '_citations': [RFC(6207)]},
 {'_': MediaType(u'application/mikey'), '_citations': [RFC(3830)]},
 {'_': MediaType(u'application/mods+xml'), '_citations': [RFC(6207)]},
 {'_': MediaType(u'application/moss-keys'), '_citations': [RFC(1848)]},
 {'_': MediaType(u'application/moss-signature'), '_citations': [RFC(1848)]},
 {'_': MediaType(u'application/mosskey-data'), '_citations': [RFC(1848)]},
 {'_': MediaType(u'application/mosskey-request'), '_citations': [RFC(1848)]},
 {'_': MediaType(u'application/mp21'), '_citations': [RFC(6381)]},
 {'_': MediaType(u'application/mp4'), '_citations': [RFC(4337), RFC(6381)]},
 {'_': MediaType(u'application/mpeg4-generic'), '_citations': [RFC(3640)]},
 {'_': MediaType(u'application/mpeg4-iod'), '_citations': [RFC(4337)]},
 {'_': MediaType(u'application/mpeg4-iod-xmt'), '_citations': [RFC(4337)]},
 {'_': MediaType(u'application/mrb-consumer+xml'), '_citations': [RFC(6917)]},
 {'_': MediaType(u'application/mrb-publish+xml'), '_citations': [RFC(6917)]},
 {'_': MediaType(u'application/msc-ivr+xml'), '_citations': [RFC(6231)]},
 {'_': MediaType(u'application/msc-mixer+xml'), '_citations': [RFC(6505)]},
 {'_': MediaType(u'application/mxf'), '_citations': [RFC(4539)]},
 {'_': MediaType(u'application/nasdata'), '_citations': [RFC(4707)]},
 {'_': MediaType(u'application/news-checkgroups'), '_citations': [RFC(5537)]},
 {'_': MediaType(u'application/news-groupinfo'), '_citations': [RFC(5537)]},
 {'_': MediaType(u'application/news-transmission'), '_citations': [RFC(5537)]},
 {'_': MediaType(u'application/nlsml+xml'), '_citations': [RFC(6787)]},
 {'_': MediaType(u'application/ocsp-request'), '_citations': [RFC(6960)]},
 {'_': MediaType(u'application/ocsp-response'), '_citations': [RFC(6960)]},
 {'_': MediaType(u'application/octet-stream'),
  '_citations': [RFC(2045), RFC(2046)]},
 {'_': MediaType(u'application/oda'), '_citations': [RFC(2045), RFC(2046)]},
 {'_': MediaType(u'application/oebps-package+xml'), '_citations': [RFC(4839)]},
 {'_': MediaType(u'application/ogg'), '_citations': [RFC(5334), RFC(7845)]},
 {'_': MediaType(u'application/p2p-overlay+xml'), '_citations': [RFC(6940)]},
 {'_': MediaType(u'application/parityfec'), '_citations': [RFC(5109)]},
 {'_': MediaType(u'application/patch-ops-error+xml'),
  '_citations': [RFC(5261)]},
 {'_': MediaType(u'application/pdf'), '_citations': [RFC(3778)]},
 {'_': MediaType(u'application/pgp-encrypted'), '_citations': [RFC(3156)]},
 {'_': MediaType(u'application/pgp-keys'), '_citations': [RFC(3156)]},
 {'_': MediaType(u'application/pgp-signature'), '_citations': [RFC(3156)]},
 {'_': MediaType(u'application/pidf-diff+xml'), '_citations': [RFC(5262)]},
 {'_': MediaType(u'application/pidf+xml'), '_citations': [RFC(3863)]},
 {'_': MediaType(u'application/pkcs10'), '_citations': [RFC(5967)]},
 {'_': MediaType(u'application/pkcs7-mime'),
  '_citations': [RFC(5751), RFC(7114)]},
 {'_': MediaType(u'application/pkcs7-signature'), '_citations': [RFC(5751)]},
 {'_': MediaType(u'application/pkcs8'), '_citations': [RFC(5958)]},
 {'_': MediaType(u'application/pkix-attr-cert'), '_citations': [RFC(5877)]},
 {'_': MediaType(u'application/pkix-cert'), '_citations': [RFC(2585)]},
 {'_': MediaType(u'application/pkix-crl'), '_citations': [RFC(2585)]},
 {'_': MediaType(u'application/pkix-pkipath'), '_citations': [RFC(6066)]},
 {'_': MediaType(u'application/pkixcmp'), '_citations': [RFC(2510)]},
 {'_': MediaType(u'application/pls+xml'), '_citations': [RFC(4267)]},
 {'_': MediaType(u'application/poc-settings+xml'), '_citations': [RFC(4354)]},
 {'_': MediaType(u'application/postscript'),
  '_citations': [RFC(2045), RFC(2046)]},
 {'_': MediaType(u'application/ppsp-tracker+json'), '_citations': [RFC(7846)]},
 {'_': MediaType(u'application/problem+json'), '_citations': [RFC(7807)]},
 {'_': MediaType(u'application/problem+xml'), '_citations': [RFC(7807)]},
 {'_': MediaType(u'application/pskc+xml'), '_citations': [RFC(6030)]},
 {'_': MediaType(u'application/rdf+xml'), '_citations': [RFC(3870)]},
 {'_': MediaType(u'application/qsig'), '_citations': [RFC(3204)]},
 {'_': MediaType(u'application/raptorfec'), '_citations': [RFC(6682)]},
 {'_': MediaType(u'application/rdap+json'), '_citations': [RFC(7483)]},
 {'_': MediaType(u'application/reginfo+xml'), '_citations': [RFC(3680)]},
 {'_': MediaType(u'application/relax-ng-compact-syntax'),
  '_citations': [Citation(None,
                          'http://www.jtc1sc34.org/repository/0661.pdf')]},
 {'_': MediaType(u'application/remote-printing'), '_citations': [RFC(1486)]},
 {'_': MediaType(u'application/reputon+json'), '_citations': [RFC(7071)]},
 {'_': MediaType(u'application/resource-lists-diff+xml'),
  '_citations': [RFC(5362)]},
 {'_': MediaType(u'application/resource-lists+xml'),
  '_citations': [RFC(4826)]},
 {'_': MediaType(u'application/rfc+xml'), '_citations': [RFC(7991)]},
 {'_': MediaType(u'application/rlmi+xml'), '_citations': [RFC(4662)]},
 {'_': MediaType(u'application/rls-services+xml'), '_citations': [RFC(4826)]},
 {'_': MediaType(u'application/rpki-ghostbusters'), '_citations': [RFC(6493)]},
 {'_': MediaType(u'application/rpki-manifest'), '_citations': [RFC(6481)]},
 {'_': MediaType(u'application/rpki-roa'), '_citations': [RFC(6481)]},
 {'_': MediaType(u'application/rpki-updown'), '_citations': [RFC(6492)]},
 {'_': MediaType(u'application/rtploopback'), '_citations': [RFC(6849)]},
 {'_': MediaType(u'application/rtx'), '_citations': [RFC(4588)]},
 {'_': MediaType(u'application/sbml+xml'), '_citations': [RFC(3823)]},
 {'_': MediaType(u'application/scim+json'), '_citations': [RFC(7644)]},
 {'_': MediaType(u'application/scvp-cv-request'), '_citations': [RFC(5055)]},
 {'_': MediaType(u'application/scvp-cv-response'), '_citations': [RFC(5055)]},
 {'_': MediaType(u'application/scvp-vp-request'), '_citations': [RFC(5055)]},
 {'_': MediaType(u'application/scvp-vp-response'), '_citations': [RFC(5055)]},
 {'_': MediaType(u'application/sdp'), '_citations': [RFC(4566)]},
 {'_': MediaType(u'application/sgml'), '_citations': [RFC(1874)]},
 {'_': MediaType(u'application/shf+xml'), '_citations': [RFC(4194)]},
 {'_': MediaType(u'application/sieve'), '_citations': [RFC(5228)]},
 {'_': MediaType(u'application/simple-filter+xml'), '_citations': [RFC(4661)]},
 {'_': MediaType(u'application/simple-message-summary'),
  '_citations': [RFC(3842)]},
 {'_': MediaType(u'application/smil'),
  '_citations': [RFC(4536)],
  'deprecated': True},
 {'_': MediaType(u'application/smil+xml'), '_citations': [RFC(4536)]},
 {'_': MediaType(u'application/smpte336m'), '_citations': [RFC(6597)]},
 {'_': MediaType(u'application/soap+xml'), '_citations': [RFC(3902)]},
 {'_': MediaType(u'application/sparql-query'),
  '_citations': [Citation(None,
                          u'http://www.w3.org/TR/2007/'
                          u'CR-rdf-sparql-query-20070614/#mediaType')]},
 {'_': MediaType(u'application/sparql-results+xml'),
  '_citations': [Citation(None,
                          u'http://www.w3.org/TR/2007/'
                          u'CR-rdf-sparql-XMLres-20070925/#mime')]},
 {'_': MediaType(u'application/spirits-event+xml'), '_citations': [RFC(3910)]},
 {'_': MediaType(u'application/sql'), '_citations': [RFC(6922)]},
 {'_': MediaType(u'application/srgs'), '_citations': [RFC(4267)]},
 {'_': MediaType(u'application/srgs+xml'), '_citations': [RFC(4267)]},
 {'_': MediaType(u'application/sru+xml'), '_citations': [RFC(6207)]},
 {'_': MediaType(u'application/ssml+xml'), '_citations': [RFC(4267)]},
 {'_': MediaType(u'application/tamp-apex-update'), '_citations': [RFC(5934)]},
 {'_': MediaType(u'application/tamp-apex-update-confirm'),
  '_citations': [RFC(5934)]},
 {'_': MediaType(u'application/tamp-community-update'),
  '_citations': [RFC(5934)]},
 {'_': MediaType(u'application/tamp-community-update-confirm'),
  '_citations': [RFC(5934)]},
 {'_': MediaType(u'application/tamp-error'), '_citations': [RFC(5934)]},
 {'_': MediaType(u'application/tamp-sequence-adjust'),
  '_citations': [RFC(5934)]},
 {'_': MediaType(u'application/tamp-sequence-adjust-confirm'),
  '_citations': [RFC(5934)]},
 {'_': MediaType(u'application/tamp-status-query'), '_citations': [RFC(5934)]},
 {'_': MediaType(u'application/tamp-status-response'),
  '_citations': [RFC(5934)]},
 {'_': MediaType(u'application/tamp-update'), '_citations': [RFC(5934)]},
 {'_': MediaType(u'application/tamp-update-confirm'),
  '_citations': [RFC(5934)]},
 {'_': MediaType(u'application/tei+xml'), '_citations': [RFC(6129)]},
 {'_': MediaType(u'application/thraud+xml'), '_citations': [RFC(5941)]},
 {'_': MediaType(u'application/timestamp-query'), '_citations': [RFC(3161)]},
 {'_': MediaType(u'application/timestamp-reply'), '_citations': [RFC(3161)]},
 {'_': MediaType(u'application/timestamped-data'), '_citations': [RFC(5955)]},
 {'_': MediaType(u'application/ulpfec'), '_citations': [RFC(5109)]},
 {'_': MediaType(u'application/vcard+json'), '_citations': [RFC(7095)]},
 {'_': MediaType(u'application/vcard+xml'), '_citations': [RFC(6351)]},
 {'_': MediaType(u'application/vemmi'), '_citations': [RFC(2122)]},
 {'_': MediaType(u'application/voicexml+xml'), '_citations': [RFC(4267)]},
 {'_': MediaType(u'application/vq-rtcpxr'), '_citations': [RFC(6035)]},
 {'_': MediaType(u'application/watcherinfo+xml'), '_citations': [RFC(3858)]},
 {'_': MediaType(u'application/whoispp-query'), '_citations': [RFC(2957)]},
 {'_': MediaType(u'application/whoispp-response'), '_citations': [RFC(2958)]},
 {'_': MediaType(u'application/widget'),
  '_citations': [Citation(u'ISO/IEC 19757-2:2003/FDAM-1',
                          u'http://www.w3.org/TR/widgets/'
                          u'#media-type-registration-for-application/widget')]},
 {'_': MediaType(u'application/x-www-form-urlencoded'),
  '_citations': [Citation(None,
                          u'http://www.w3.org/TR/html/iana.html'
                          u'#application/x-www-form-urlencoded')],
  'patch': False},
 {'_': MediaType(u'application/x400-bp'), '_citations': [RFC(1494)]},
 {'_': MediaType(u'application/xacml+xml'), '_citations': [RFC(7061)]},
 {'_': MediaType(u'application/xcap-att+xml'), '_citations': [RFC(4825)]},
 {'_': MediaType(u'application/xcap-caps+xml'), '_citations': [RFC(4825)]},
 {'_': MediaType(u'application/xcap-diff+xml'), '_citations': [RFC(5874)]},
 {'_': MediaType(u'application/xcap-el+xml'), '_citations': [RFC(4825)]},
 {'_': MediaType(u'application/xcap-error+xml'), '_citations': [RFC(4825)]},
 {'_': MediaType(u'application/xcap-ns+xml'), '_citations': [RFC(4825)]},
 {'_': MediaType(u'application/xcon-conference-info-diff+xml'),
  '_citations': [RFC(6502)]},
 {'_': MediaType(u'application/xcon-conference-info+xml'),
  '_citations': [RFC(6502)]},
 {'_': MediaType(u'application/xhtml+xml'),
  '_citations': [Citation(None,
                          u'http://www.w3.org/TR/'
                          u'html/iana.html#application/xhtml+xml')]},
 {'_': MediaType(u'application/xml'),
  '_citations': [RFC(7303)],
  'is_xml': True,
  'patch': False},
 {'_': MediaType(u'application/xml-dtd'), '_citations': [RFC(7303)]},
 {'_': MediaType(u'application/xml-external-parsed-entity'),
  '_citations': [RFC(7303)]},
 {'_': MediaType(u'application/xml-patch+xml'), '_citations': [RFC(7351)],
  'patch': True},
 {'_': MediaType(u'application/xmpp+xml'), '_citations': [RFC(3923)]},
 {'_': MediaType(u'application/xslt+xml'),
  '_citations': [Citation(None,
                          u'http://www.w3.org/TR/2007/'
                          u'REC-xslt20-20070123/#media-type-registration')]},
 {'_': MediaType(u'application/xv+xml'), '_citations': [RFC(4374)]},
 {'_': MediaType(u'application/yang'), '_citations': [RFC(6020)]},
 {'_': MediaType(u'application/yin+xml'), '_citations': [RFC(6020)]},
 {'_': MediaType(u'application/zlib'), '_citations': [RFC(6713)]},
 {'_': MediaType(u'audio/1d-interleaved-parityfec'),
  '_citations': [RFC(6015)]},
 {'_': MediaType(u'audio/32kadpcm'), '_citations': [RFC(3802), RFC(2421)]},
 {'_': MediaType(u'audio/3gpp'), '_citations': [RFC(3839), RFC(6381)]},
 {'_': MediaType(u'audio/3gpp2'), '_citations': [RFC(4393), RFC(6381)]},
 {'_': MediaType(u'audio/ac3'), '_citations': [RFC(4184)]},
 {'_': MediaType(u'audio/amr'), '_citations': [RFC(4867)]},
 {'_': MediaType(u'audio/amr-wb'), '_citations': [RFC(4867)]},
 {'_': MediaType(u'audio/amr-wb+'), '_citations': [RFC(4352)]},
 {'_': MediaType(u'audio/aptx'), '_citations': [RFC(7310)]},
 {'_': MediaType(u'audio/asc'), '_citations': [RFC(6295)]},
 {'_': MediaType(u'audio/atrac-advanced-lossless'), '_citations': [RFC(5584)]},
 {'_': MediaType(u'audio/atrac-x'), '_citations': [RFC(5584)]},
 {'_': MediaType(u'audio/atrac3'), '_citations': [RFC(5584)]},
 {'_': MediaType(u'audio/basic'), '_citations': [RFC(2045), RFC(2046)]},
 {'_': MediaType(u'audio/bv16'), '_citations': [RFC(4298)]},
 {'_': MediaType(u'audio/bv32'), '_citations': [RFC(4298)]},
 {'_': MediaType(u'audio/clearmode'), '_citations': [RFC(4040)]},
 {'_': MediaType(u'audio/cn'), '_citations': [RFC(3389)]},
 {'_': MediaType(u'audio/dat12'), '_citations': [RFC(3190)]},
 {'_': MediaType(u'audio/dls'), '_citations': [RFC(4613)]},
 {'_': MediaType(u'audio/dsr-es201108'), '_citations': [RFC(3557)]},
 {'_': MediaType(u'audio/dsr-es202050'), '_citations': [RFC(4060)]},
 {'_': MediaType(u'audio/dsr-es202211'), '_citations': [RFC(4060)]},
 {'_': MediaType(u'audio/dsr-es202212'), '_citations': [RFC(4060)]},
 {'_': MediaType(u'audio/dv'), '_citations': [RFC(6469)]},
 {'_': MediaType(u'audio/dvi4'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/eac3'), '_citations': [RFC(4598)]},
 {'_': MediaType(u'audio/encaprtp'), '_citations': [RFC(6849)]},
 {'_': MediaType(u'audio/evrc'), '_citations': [RFC(4788)]},
 {'_': MediaType(u'audio/evrc-qcp'), '_citations': [RFC(3625)]},
 {'_': MediaType(u'audio/evrc0'), '_citations': [RFC(4788)]},
 {'_': MediaType(u'audio/evrc1'), '_citations': [RFC(4788)]},
 {'_': MediaType(u'audio/evrcb'), '_citations': [RFC(5188)]},
 {'_': MediaType(u'audio/evrcb0'), '_citations': [RFC(5188)]},
 {'_': MediaType(u'audio/evrcb1'), '_citations': [RFC(4788)]},
 {'_': MediaType(u'audio/evrcnw'), '_citations': [RFC(6884)]},
 {'_': MediaType(u'audio/evrcnw0'), '_citations': [RFC(6884)]},
 {'_': MediaType(u'audio/evrcnw1'), '_citations': [RFC(6884)]},
 {'_': MediaType(u'audio/evrcwb'), '_citations': [RFC(5188)]},
 {'_': MediaType(u'audio/evrcwb0'), '_citations': [RFC(5188)]},
 {'_': MediaType(u'audio/evrcwb1'), '_citations': [RFC(5188)]},
 {'_': MediaType(u'audio/example'), '_citations': [RFC(4735)]},
 {'_': MediaType(u'audio/fwdred'), '_citations': [RFC(6354)]},
 {'_': MediaType(u'audio/g711-0'), '_citations': [RFC(7655)]},
 {'_': MediaType(u'audio/g719'), '_citations': [RFC(5404)]},
 {'_': MediaType(u'audio/g7221'), '_citations': [RFC(5577)]},
 {'_': MediaType(u'audio/g722'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/g723'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/g726-16'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/g726-24'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/g726-32'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/g726-40'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/g728'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/g729'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/g7291'), '_citations': [RFC(4749), RFC(5459)]},
 {'_': MediaType(u'audio/g729d'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/g729e'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/gsm'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/gsm-efr'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/gsm-hr-08'), '_citations': [RFC(5993)]},
 {'_': MediaType(u'audio/ilbc'), '_citations': [RFC(3952)]},
 {'_': MediaType(u'audio/ip-mr_v2.5'), '_citations': [RFC(6262)]},
 {'_': MediaType(u'audio/l8'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/l16'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/l20'), '_citations': [RFC(3190)]},
 {'_': MediaType(u'audio/l24'), '_citations': [RFC(3190)]},
 {'_': MediaType(u'audio/lpc'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/mobile-xmf'), '_citations': [RFC(4723)]},
 {'_': MediaType(u'audio/mpa'), '_citations': [RFC(3555)]},
 {'_': MediaType(u'audio/mp4'), '_citations': [RFC(4337), RFC(6381)]},
 {'_': MediaType(u'audio/mp4a-latm'), '_citations': [RFC(6416)]},
 {'_': MediaType(u'audio/mpa-robust'), '_citations': [RFC(5219)]},
 {'_': MediaType(u'audio/mpeg'), '_citations': [RFC(3003)]},
 {'_': MediaType(u'audio/mpeg4-generic'),
  '_citations': [RFC(3640), RFC(5691), RFC(6295)]},
 {'_': MediaType(u'audio/ogg'), '_citations': [RFC(5334), RFC(7845)]},
 {'_': MediaType(u'audio/opus'), '_citations': [RFC(7587)]},
 {'_': MediaType(u'audio/parityfec'), '_citations': [RFC(5109)]},
 {'_': MediaType(u'audio/pcma'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/pcma-wb'), '_citations': [RFC(5391)]},
 {'_': MediaType(u'audio/pcmu'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/pcmu-wb'), '_citations': [RFC(5391)]},
 {'_': MediaType(u'audio/qcelp'), '_citations': [RFC(3555), RFC(3625)]},
 {'_': MediaType(u'audio/raptorfec'), '_citations': [RFC(6682)]},
 {'_': MediaType(u'audio/red'), '_citations': [RFC(3555)]},
 {'_': MediaType(u'audio/rtploopback'), '_citations': [RFC(6849)]},
 {'_': MediaType(u'audio/rtp-midi'), '_citations': [RFC(6295)]},
 {'_': MediaType(u'audio/rtx'), '_citations': [RFC(4588)]},
 {'_': MediaType(u'audio/smv'), '_citations': [RFC(3558)]},
 {'_': MediaType(u'audio/smv0'), '_citations': [RFC(3558)]},
 {'_': MediaType(u'audio/smv-qcp'), '_citations': [RFC(3625)]},
 {'_': MediaType(u'audio/speex'), '_citations': [RFC(5574)]},
 {'_': MediaType(u'audio/t140c'), '_citations': [RFC(4351)]},
 {'_': MediaType(u'audio/t38'), '_citations': [RFC(4612)]},
 {'_': MediaType(u'audio/telephone-event'), '_citations': [RFC(4733)]},
 {'_': MediaType(u'audio/tone'), '_citations': [RFC(4733)]},
 {'_': MediaType(u'audio/uemclip'), '_citations': [RFC(5686)]},
 {'_': MediaType(u'audio/ulpfec'), '_citations': [RFC(5109)]},
 {'_': MediaType(u'audio/vdvi'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'audio/vmr-wb'), '_citations': [RFC(4348), RFC(4424)]},
 {'_': MediaType(u'audio/vorbis'), '_citations': [RFC(5215)]},
 {'_': MediaType(u'audio/vorbis-config'), '_citations': [RFC(5215)]},
 {'_': MediaType(u'image/bmp'), '_citations': [RFC(7903)]},
 {'_': MediaType(u'image/emf'), '_citations': [RFC(7903)]},
 {'_': MediaType(u'image/example'), '_citations': [RFC(4735)]},
 {'_': MediaType(u'image/fits'), '_citations': [RFC(4047)]},
 {'_': MediaType(u'image/g3fax'), '_citations': [RFC(1494)]},
 {'_': MediaType(u'image/gif'), '_citations': [RFC(2045), RFC(2046)]},
 {'_': MediaType(u'image/ief'), '_citations': [RFC(1314)]},
 {'_': MediaType(u'image/jp2'), '_citations': [RFC(3745)]},
 {'_': MediaType(u'image/jpeg'), '_citations': [RFC(2045), RFC(2046)]},
 {'_': MediaType(u'image/jpm'), '_citations': [RFC(3745)]},
 {'_': MediaType(u'image/jpx'), '_citations': [RFC(3745)]},
 {'_': MediaType(u'image/ktx'),
  '_citations': [Citation(None,
                          u'http://www.khronos.org/opengles/sdk/'
                          u'tools/KTX/file_format_spec/#mimeregistration')]},
 {'_': MediaType(u'image/svg+xml'),
  '_citations': [Citation(None, u'http://www.w3.org/TR/SVG/mimereg.html')]},
 {'_': MediaType(u'image/t38'), '_citations': [RFC(3362)]},
 {'_': MediaType(u'image/tiff'), '_citations': [RFC(3302)]},
 {'_': MediaType(u'image/tiff-fx'), '_citations': [RFC(3950)]},
 {'_': MediaType(u'image/wmf'), '_citations': [RFC(7903)]},
 {'_': MediaType(u'image/x-emf'),
  '_citations': [RFC(7903)],
  'deprecated': True},
 {'_': MediaType(u'image/x-wmf'),
  '_citations': [RFC(7903)],
  'deprecated': True},
 {'_': MediaType(u'message/cpim'), '_citations': [RFC(3862)]},
 {'_': MediaType(u'message/delivery-status'), '_citations': [RFC(1894)]},
 {'_': MediaType(u'message/disposition-notification'),
  '_citations': [RFC(3798)]},
 {'_': MediaType(u'message/example'), '_citations': [RFC(4735)]},
 {'_': MediaType(u'message/external-body'),
  '_citations': [RFC(2045), RFC(2046)]},
 {'_': MediaType(u'message/feedback-report'), '_citations': [RFC(5965)]},
 {'_': MediaType(u'message/global'), '_citations': [RFC(6532)]},
 {'_': MediaType(u'message/global-delivery-status'),
  '_citations': [RFC(6533)]},
 {'_': MediaType(u'message/global-disposition-notification'),
  '_citations': [RFC(6533)]},
 {'_': MediaType(u'message/global-headers'), '_citations': [RFC(6533)]},
 {'_': MediaType(u'message/http'), '_citations': [RFC(7230)]},
 {'_': MediaType(u'message/imdn+xml'), '_citations': [RFC(5438)]},
 {'_': MediaType(u'message/news'),
  '_citations': [RFC(5537)],
  'deprecated': True},
 {'_': MediaType(u'message/partial'), '_citations': [RFC(2045), RFC(2046)]},
 {'_': MediaType(u'message/rfc822'), '_citations': [RFC(2045), RFC(2046)]},
 {'_': MediaType(u'message/s-http'), '_citations': [RFC(2660)]},
 {'_': MediaType(u'message/sip'), '_citations': [RFC(3261)]},
 {'_': MediaType(u'message/sipfrag'), '_citations': [RFC(3420)]},
 {'_': MediaType(u'message/tracking-status'), '_citations': [RFC(3886)]},
 {'_': MediaType(u'model/example'), '_citations': [RFC(4735)]},
 {'_': MediaType(u'model/mesh'), '_citations': [RFC(2077)]},
 {'_': MediaType(u'model/vrml'), '_citations': [RFC(2077)]},
 {'_': MediaType(u'multipart/alternative'),
  '_citations': [RFC(2046), RFC(2045)]},
 {'_': MediaType(u'multipart/byteranges'),
  '_citations': [RFC(7233, appendix=('A',))]},
 {'_': MediaType(u'multipart/digest'), '_citations': [RFC(2046), RFC(2045)]},
 {'_': MediaType(u'multipart/encrypted'), '_citations': [RFC(1847)]},
 {'_': MediaType(u'multipart/example'), '_citations': [RFC(4735)]},
 {'_': MediaType(u'multipart/form-data'), '_citations': [RFC(7578)]},
 {'_': MediaType(u'multipart/mixed'), '_citations': [RFC(2046), RFC(2045)]},
 {'_': MediaType(u'multipart/parallel'), '_citations': [RFC(2046), RFC(2045)]},
 {'_': MediaType(u'multipart/related'), '_citations': [RFC(2387)]},
 {'_': MediaType(u'multipart/report'), '_citations': [RFC(6522)]},
 {'_': MediaType(u'multipart/signed'), '_citations': [RFC(1847)]},
 {'_': MediaType(u'multipart/voice-message'), '_citations': [RFC(3801)]},
 {'_': MediaType(u'multipart/x-mixed-replace'),
  '_citations': [Citation(None,
                          u'http://www.w3.org/TR/'
                          u'html/iana.html#multipart/x-mixed-replace')]},
 {'_': MediaType(u'text/1d-interleaved-parityfec'), '_citations': [RFC(6015)]},
 {'_': MediaType(u'text/cache-manifest'),
  '_citations': [Citation(None,
                          u'http://www.w3.org/TR/'
                          u'html/iana.html#text/cache-manifest')]},
 {'_': MediaType(u'text/calendar'), '_citations': [RFC(5545)]},
 {'_': MediaType(u'text/css'), '_citations': [RFC(2318)]},
 {'_': MediaType(u'text/csv'), '_citations': [RFC(4180), RFC(7111)]},
 {'_': MediaType(u'text/directory'),
  '_citations': [RFC(2425), RFC(6350)],
  'deprecated': True},
 {'_': MediaType(u'text/dns'), '_citations': [RFC(4027)]},
 {'_': MediaType(u'text/ecmascript'),
  '_citations': [RFC(4329)],
  'deprecated': True},
 {'_': MediaType(u'text/encaprtp'), '_citations': [RFC(6849)]},
 {'_': MediaType(u'text/enriched'), '_citations': [RFC(1896)]},
 {'_': MediaType(u'text/event-stream'),
  '_citations': [Citation(u'Server-Sent Events',
                          u'https://www.w3.org/TR/eventsource/'
                          u'#text-event-stream')],
  'patch': False},
 {'_': MediaType(u'text/example'), '_citations': [RFC(4735)]},
 {'_': MediaType(u'text/fwdred'), '_citations': [RFC(6354)]},
 {'_': MediaType(u'text/grammar-ref-list'), '_citations': [RFC(6787)]},
 {'_': MediaType(u'text/html'),
  '_citations': [Citation(None,
                          u'http://www.w3.org/TR/html/iana.html#text/html')],
  'patch': False},
 {'_': MediaType(u'text/javascript'),
  '_citations': [RFC(4329)],
  'deprecated': True},
 {'_': MediaType(u'text/markdown'), '_citations': [RFC(7763)]},
 {'_': MediaType(u'text/parameters'), '_citations': [RFC(7826)]},
 {'_': MediaType(u'text/parityfec'), '_citations': [RFC(5109)]},
 {'_': MediaType(u'text/plain'),
  '_citations': [RFC(2046), RFC(3676), RFC(5147)],
  'patch': False},
 {'_': MediaType(u'text/raptorfec'), '_citations': [RFC(6682)]},
 {'_': MediaType(u'text/red'), '_citations': [RFC(4102)]},
 {'_': MediaType(u'text/rfc822-headers'), '_citations': [RFC(6522)]},
 {'_': MediaType(u'text/richtext'), '_citations': [RFC(2045), RFC(2046)]},
 {'_': MediaType(u'text/rtploopback'), '_citations': [RFC(6849)]},
 {'_': MediaType(u'text/rtx'), '_citations': [RFC(4588)]},
 {'_': MediaType(u'text/sgml'), '_citations': [RFC(1874)]},
 {'_': MediaType(u'text/t140'), '_citations': [RFC(4103)]},
 {'_': MediaType(u'text/troff'), '_citations': [RFC(4263)]},
 {'_': MediaType(u'text/ulpfec'), '_citations': [RFC(5109)]},
 {'_': MediaType(u'text/uri-list'), '_citations': [RFC(2483)]},
 {'_': MediaType(u'text/vcard'), '_citations': [RFC(6350)]},
 {'_': MediaType(u'text/xml'),
  '_citations': [RFC(7303)],
  'is_xml': True,
  'patch': False},
 {'_': MediaType(u'text/xml-external-parsed-entity'),
  '_citations': [RFC(7303)]},
 {'_': MediaType(u'video/1d-interleaved-parityfec'),
  '_citations': [RFC(6015)]},
 {'_': MediaType(u'video/3gpp'), '_citations': [RFC(3839), RFC(6381)]},
 {'_': MediaType(u'video/3gpp2'), '_citations': [RFC(4393), RFC(6381)]},
 {'_': MediaType(u'video/3gpp-tt'), '_citations': [RFC(4396)]},
 {'_': MediaType(u'video/bmpeg'), '_citations': [RFC(3555)]},
 {'_': MediaType(u'video/bt656'), '_citations': [RFC(3555)]},
 {'_': MediaType(u'video/celb'), '_citations': [RFC(3555)]},
 {'_': MediaType(u'video/dv'), '_citations': [RFC(6469)]},
 {'_': MediaType(u'video/encaprtp'), '_citations': [RFC(6849)]},
 {'_': MediaType(u'video/example'), '_citations': [RFC(4735)]},
 {'_': MediaType(u'video/h261'), '_citations': [RFC(4587)]},
 {'_': MediaType(u'video/h263'), '_citations': [RFC(3555)]},
 {'_': MediaType(u'video/h263-1998'), '_citations': [RFC(4629)]},
 {'_': MediaType(u'video/h263-2000'), '_citations': [RFC(4629)]},
 {'_': MediaType(u'video/h264'), '_citations': [RFC(6184)]},
 {'_': MediaType(u'video/h264-rcdo'), '_citations': [RFC(6185)]},
 {'_': MediaType(u'video/h264-svc'), '_citations': [RFC(6190)]},
 {'_': MediaType(u'video/h265'), '_citations': [RFC(7798)]},
 {'_': MediaType(u'video/jpeg'), '_citations': [RFC(3555)]},
 {'_': MediaType(u'video/jpeg2000'), '_citations': [RFC(5371), RFC(5372)]},
 {'_': MediaType(u'video/mj2'), '_citations': [RFC(3745)]},
 {'_': MediaType(u'video/mp1s'), '_citations': [RFC(3555)]},
 {'_': MediaType(u'video/mp2p'), '_citations': [RFC(3555)]},
 {'_': MediaType(u'video/mp2t'), '_citations': [RFC(3555)]},
 {'_': MediaType(u'video/mp4'), '_citations': [RFC(4337), RFC(6381)]},
 {'_': MediaType(u'video/mp4v-es'), '_citations': [RFC(6416)]},
 {'_': MediaType(u'video/mpv'), '_citations': [RFC(3555)]},
 {'_': MediaType(u'video/mpeg'), '_citations': [RFC(2045), RFC(2046)]},
 {'_': MediaType(u'video/mpeg4-generic'), '_citations': [RFC(3640)]},
 {'_': MediaType(u'video/nv'), '_citations': [RFC(4856)]},
 {'_': MediaType(u'video/ogg'), '_citations': [RFC(5334), RFC(7845)]},
 {'_': MediaType(u'video/parityfec'), '_citations': [RFC(5109)]},
 {'_': MediaType(u'video/pointer'), '_citations': [RFC(2862)]},
 {'_': MediaType(u'video/quicktime'), '_citations': [RFC(6381)]},
 {'_': MediaType(u'video/raptorfec'), '_citations': [RFC(6682)]},
 {'_': MediaType(u'video/raw'), '_citations': [RFC(4175)]},
 {'_': MediaType(u'video/rtploopback'), '_citations': [RFC(6849)]},
 {'_': MediaType(u'video/rtx'), '_citations': [RFC(4588)]},
 {'_': MediaType(u'video/smpte292m'), '_citations': [RFC(3497)]},
 {'_': MediaType(u'video/ulpfec'), '_citations': [RFC(5109)]},
 {'_': MediaType(u'video/vc1'), '_citations': [RFC(4425)]},
 {'_': MediaType(u'video/vp8'), '_citations': [RFC(7741)]},
], extra_info=['deprecated', 'is_json', 'is_xml', 'patch'])
