import json
import unittest

from django.core.urlresolvers import reverse
from django.test import Client

import example_app.views


class ExampleTestCase(unittest.TestCase):

    def test_get_json(self):
        response = Client().get(reverse(example_app.views.my_view),
                                {'format': 'json', 'name': u'Martha'})
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['hello'], u'Martha')

    def test_get_plain(self):
        response = Client().get(reverse(example_app.views.my_view),
                                {'format': 'plain', 'name': u'Martha'})
        self.assertEqual(response.content, b'Hello Martha!\n')

    def test_no_params(self):
        response = Client().get(reverse(example_app.views.my_view))
        self.assertEqual(response.status_code, 200)
