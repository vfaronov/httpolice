# -*- coding: utf-8; -*-

from django.conf import settings
from django.utils import six


DEFAULT_SETTINGS = {
    'HTTPOLICE_ENABLE': False,
    'HTTPOLICE_BACKLOG': 20,
    'HTTPOLICE_SILENCE': [1110],
    'HTTPOLICE_RAISE': False,
}


def get_setting(name):
    name = 'HTTPOLICE_' + name
    return getattr(settings, name, DEFAULT_SETTINGS[name])


class ProtocolError(Exception):

    """A protocol error in a response produced by the application."""

    def __init__(self, exchange):
        # Importing `httpolice` can execute a lot of code,
        # so we only do it when it's really time for action.
        import httpolice
        buf = six.BytesIO()
        httpolice.text_report([exchange], buf)
        super(ProtocolError, self).__init__(
            u'HTTPolice found errors in this response:\n' +
            buf.getvalue().decode('utf-8')
        )
