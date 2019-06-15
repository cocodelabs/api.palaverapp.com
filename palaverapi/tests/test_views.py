import unittest
import json
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

        push_token = Token.select().where(Token.device == device, Token.token == 'ec1752bd70320e4763f7165d73e2636cca9e25cf').get()
        token = Token.select().where(Token.device == device, Token.token == 'test_token').get()

        token.delete_instance()
        push_token.delete_instance()
        device.delete_instance()

    def test_returns_200_when_re_registering(self):
        response = self.client.post('/1/devices', {'device_token': 'test_token'})
        response = self.client.post('/1/devices', {'device_token': 'test_token'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(response.content, '{"device_token": "test_token", "push_token": "ec1752bd70320e4763f7165d73e2636cca9e25cf"}')

        device = Device.get(apns_token='test_token')
        assert device

        push_token = Token.select().where(Token.device == device, Token.token == 'ec1752bd70320e4763f7165d73e2636cca9e25cf').get()
        token = Token.select().where(Token.device == device, Token.token == 'test_token').get()

        push_token.delete_instance()
        token.delete_instance()
        device.delete_instance()

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

        token.delete_instance()
        device.delete_instance()


class AuthorisationListViewTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(router)

        self.device = Device.create(apns_token='ec1752bd70320e4763f7165d73e2636cca9e25cf')
        self.token = Token.create(device=self.device, token='e4763f7165d73e2636cca9e', scope=Token.ALL_SCOPE)

    def tearDown(self):
        self.token.delete_instance()
        self.device.delete_instance()

    def test_list(self):
        headers = { 'AUTHORIZATION': 'token e4763f7165d73e2636cca9e' }
        response = self.client.get('/authorisations', {}, headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), [
            {
                'url': '/authorisations/636cca9e',
                'scopes': ['all'],
                'token_last_eight': '636cca9e'
            }
        ])

    def test_create(self):
        headers = { 'AUTHORIZATION': 'token e4763f7165d73e2636cca9e' }
        response = self.client.post('/authorisations', {}, headers)

        self.assertEqual(response.status_code, 201)

        content = json.loads(response.content)
        self.assertTrue('url' in content)
        self.assertTrue('token' in content)
        self.assertTrue('token_last_eight' in content)
        #self.assertEqual(len('token_last_eight'), 8)
        self.assertTrue('scopes' in content)
        self.assertEqual(content['scopes'], ['all'])

        token = Token.select().where(Token.token == content['token']).get()
        token.delete_instance()

    def test_create_with_scope(self):
        headers = { 'AUTHORIZATION': 'token e4763f7165d73e2636cca9e' }
        response = self.client.post('/authorisations', {'scopes': ['push']}, headers)

        self.assertEqual(response.status_code, 201)

        content = json.loads(response.content)
        self.assertTrue('url' in content)
        self.assertTrue('token' in content)
        self.assertTrue('token_last_eight' in content)
        #self.assertEqual(len('token_last_eight'), 8)
        self.assertTrue('scopes' in content)
        #self.assertEqual(content['scopes'], ['push'])

        token = Token.select().where(Token.token == content['token']).get()
        token.delete_instance()

    def test_create_with_token(self):
        headers = { 'AUTHORIZATION': 'token e4763f7165d73e2636cca9e' }
        response = self.client.post('/authorisations', {'token': '4876f9ca0d91362fae6cd4f9cde5d0044295682e'}, headers)

        self.assertEqual(response.status_code, 201)

        content = json.loads(response.content)
        self.assertTrue('url' in content)
        self.assertTrue('token' in content)
        self.assertTrue('token_last_eight' in content)
        #self.assertEqual(len('token_last_eight'), 8)
        self.assertTrue('scopes' in content)
        self.assertEqual(content['token'], '4876f9ca0d91362fae6cd4f9cde5d0044295682e')

        token = Token.select().where(Token.token == content['token']).get()
        token.delete_instance()

    def test_returns_200_when_re_registering(self):
        headers = { 'AUTHORIZATION': 'token e4763f7165d73e2636cca9e' }
        response = self.client.post('/authorisations', {'token': '4876f9ca0d91362fae6cd4f9cde5d0044295682e'}, headers)
        response = self.client.post('/authorisations', {'token': '4876f9ca0d91362fae6cd4f9cde5d0044295682e'}, headers)

        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)
        self.assertTrue('url' in content)
        self.assertTrue('token' in content)
        self.assertTrue('token_last_eight' in content)
        #self.assertEqual(len('token_last_eight'), 8)
        self.assertTrue('scopes' in content)
        self.assertEqual(content['token'], '4876f9ca0d91362fae6cd4f9cde5d0044295682e')

        token = Token.select().where(Token.token == content['token']).get()
        token.delete_instance()


class AuthorisationDetailViewTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(router)

        self.device = Device.create(apns_token='ec1752bd70320e4763f7165d73e2636cca9e25cf')
        self.token = Token.create(device=self.device, token='e4763f7165d73e2636cca9e', scope=Token.ALL_SCOPE)

    def tearDown(self):
        if self.token:
            self.token.delete_instance()

        self.device.delete_instance()

    def test_get(self):
        headers = { 'AUTHORIZATION': 'token e4763f7165d73e2636cca9e' }
        response = self.client.get('/authorisations/636cca9e', {}, headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {
            'url': '/authorisations/636cca9e',
            'scopes': ['all'],
            'token_last_eight': '636cca9e'
        })

    def test_delete(self):
        headers = { 'AUTHORIZATION': 'token e4763f7165d73e2636cca9e' }
        response = self.client.delete('/authorisations/636cca9e', {}, headers)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(Token.select().count(), 0)

        self.token = None
