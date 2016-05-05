# Change Log

All notable changes to HTTPolice will be documented in this file.

This project adheres to [Semantic Versioning](http://semver.org/)
(which means it is unstable until 1.0).


## Unreleased

### Added
- Django integration (as a separate distribution; see docs).
- Unwanted notices can now be [silenced][].
- Checks for the Content-Disposition header (RFC 6266).
- Checks for RFC 5987 encoded values.
- Checks for alternative services (RFC 7838).
- Checks for HTTP/1.1 connection control features prohibited in HTTP/2.
- Checks for status code 451 (Unavailable For Legal Reasons; RFC 7725).

[silenced]: http://pythonhosted.org/HTTPolice/concepts.html#silence

### Changed
- mitmproxy integration has been moved into a separate distribution (see docs).
- Stale controls (RFC 5861) are now recognized.

### Deprecated

### Removed

### Fixed
- Input files from tcpick are sorted correctly.
- Notice 1108 (wrong day of week) doesn't crash in non-English locales.
- Notice 1038 (bad JSON body) and such are not reported on responses to HEAD.

### Security


## 0.1.0 - 2016-04-25

### Added
- Initial release.
