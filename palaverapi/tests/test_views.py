import unittest
from rivr.tests import TestClient

from palaverapi.views import router, queue
from palaverapi.models import Device, Token


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(router)

    def test_status(self):
        assert self.client.get('/').status_code is 204

    def test_register(self):
        response = self.client.post('/1/devices', {'device_token': 'test_token'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(response.content, '{"device_token": "test_token", "push_token": "ec1752bd70320e4763f7165d73e2636cca9e25cf"}')

        device = Device.get(apns_token='test_token')
        assert device

        push_token = Token.select().where(Token.device == device, Token.token == 'ec1752bd70320e4763f7165d73e2636cca9e25cf')
        token = Token.select().where(Token.device == device, Token.token == 'test_token')
        assert token.get()
        assert push_token.get()

    def test_returns_200_when_re_registering(self):
        response = self.client.post('/1/devices', {'device_token': 'test_token'})
        response = self.client.post('/1/devices', {'device_token': 'test_token'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(response.content, '{"device_token": "test_token", "push_token": "ec1752bd70320e4763f7165d73e2636cca9e25cf"}')

        device = Device.get(apns_token='test_token')
        assert device

        push_token = Token.select().where(Token.device == device, Token.token == 'ec1752bd70320e4763f7165d73e2636cca9e25cf')
        token = Token.select().where(Token.device == device, Token.token == 'test_token')
        assert token.get()
        assert push_token.get()

    def test_push_401_missing_token(self):
        response = self.client.post('/1/push', {})
        self.assertEqual(response.status_code, 401)

    def test_push(self):
        enqueued = []

        def enqueue(*args):
            enqueued.append(args)
        queue.enqueue = enqueue

        device = Device.create(apns_token='ec1752bd70320e4763f7165d73e2636cca9e25cf')
        token = Token.create(device=device, token='valid', scope=Token.ALL_SCOPE)

        headers = { 'AUTHORIZATION': 'token valid' }
        response = self.client.post('/1/push', {}, headers)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(enqueued), 1)

    def test_push_with_network_uuid_in_token(self):
        enqueued = []

        def enqueue(*args):
            enqueued.append(args)
        queue.enqueue = enqueue

        device = Device.create(apns_token='ec1752bd70320e4763f7165d73e2636cca9e25cf')
        token = Token.create(device=device, token='valid', scope=Token.ALL_SCOPE)

        headers = { 'AUTHORIZATION': 'token valid/network-uuid' }
        response = self.client.post('/1/push', {}, headers)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(enqueued), 1)
