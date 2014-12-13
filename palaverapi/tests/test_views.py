import unittest
from rivr.tests import TestClient

from palaverapi.views import router
from palaverapi.models import Device, Token


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(router)

    def test_status(self):
        assert self.client.get('/').status_code is 204

    def test_register(self):
        response = self.client.post('/1/devices', {'device_token': 'test_token'})
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(response.content, '{"device_token": "test_token", "push_token": "ec1752bd70320e4763f7165d73e2636cca9e25cf"}')

        device = Device.get(apns_token='test_token')
        tokens = Token.select().where(Token.device == device)
        self.assertEqual(tokens.count(), 2)

