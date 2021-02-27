import unittest
import json

from rivr.test import Client

from palaverapi.views import app


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.client = Client(app)

    def test_404(self):
        response = self.client.get('/404')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers['Content-Type'], 'application/problem+json')
        self.assertEqual(response.content, '{"title": "Resource Not Found"}')

    def test_500(self):
        response = self.client.get('/500')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.headers['Content-Type'], 'application/problem+json')
        self.assertEqual(response.content, '{"title": "Internal Server Error"}')
