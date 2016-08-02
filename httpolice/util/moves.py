# -*- coding: utf-8; -*-
# pylint: disable=unused-import

# These are like `six.moves`, but we cannot add them with `six.add_move`
# because we are a library and we must not touch that shared namespace.

try:        # pragma: no cover
    from email import message_from_bytes
except ImportError:                       # Python 2; pragma: no cover
    from email import message_from_string as message_from_bytes

try:        # pragma: no cover
    from urllib.parse import unquote_to_bytes
except ImportError:                       # Python 2; pragma: no cover
    from urllib import unquote as unquote_to_bytes
