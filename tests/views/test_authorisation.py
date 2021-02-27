import json
import unittest

from rivr.test import Client

from palaverapi import app
from palaverapi.models import Device, Token


class AuthorisationListViewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = Client(app)

        self.device = Device.create(
            apns_token='ec1752bd70320e4763f7165d73e2636cca9e25cf'
        )
        self.token = Token.create(
            device=self.device, token='e4763f7165d73e2636cca9e', scope=Token.ALL_SCOPE
        )

    def tearDown(self) -> None:
        self.token.delete_instance()
        self.device.delete_instance()

    def test_list(self) -> None:
        headers = {'AUTHORIZATION': 'token e4763f7165d73e2636cca9e'}
        response = self.client.get('/authorisations', {}, headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            [
                {
                    'url': '/authorisations/636cca9e',
                    'scopes': ['all'],
                    'token_last_eight': '636cca9e',
                }
            ],
        )

    def test_create(self) -> None:
        headers = {'AUTHORIZATION': 'token e4763f7165d73e2636cca9e'}
        response = self.client.post('/authorisations', headers=headers)

        self.assertEqual(response.status_code, 201)

        content = json.loads(response.content)
        self.assertTrue('url' in content)
        self.assertTrue('token' in content)
        self.assertTrue('token_last_eight' in content)
        # self.assertEqual(len('token_last_eight'), 8)
        self.assertTrue('scopes' in content)
        self.assertEqual(content['scopes'], ['all'])

        token = Token.select().where(Token.token == content['token']).get()
        token.delete_instance()

    def test_create_with_scope(self) -> None:
        headers = {
            'AUTHORIZATION': 'token e4763f7165d73e2636cca9e',
            'Content-Type': 'application/json',
        }
        response = self.client.post(
            '/authorisations',
            headers=headers,
            body=json.dumps({'scopes': ['push']}).encode('utf-8'),
        )

        self.assertEqual(response.status_code, 201)

        content = json.loads(response.content)
        self.assertTrue('url' in content)
        self.assertTrue('token' in content)
        self.assertTrue('token_last_eight' in content)
        # self.assertEqual(len('token_last_eight'), 8)
        self.assertTrue('scopes' in content)
        # self.assertEqual(content['scopes'], ['push'])

        token = Token.select().where(Token.token == content['token']).get()
        token.delete_instance()

    def test_create_with_token(self) -> None:
        headers = {
            'AUTHORIZATION': 'token e4763f7165d73e2636cca9e',
            'Content-Type': 'application/json',
        }
        response = self.client.post(
            '/authorisations',
            headers=headers,
            body=json.dumps(
                {'token': '4876f9ca0d91362fae6cd4f9cde5d0044295682e'}
            ).encode('utf-8'),
        )

        self.assertEqual(response.status_code, 201)

        content = json.loads(response.content)
        self.assertTrue('url' in content)
        self.assertTrue('token' in content)
        self.assertTrue('token_last_eight' in content)
        # self.assertEqual(len('token_last_eight'), 8)
        self.assertTrue('scopes' in content)
        self.assertEqual(content['token'], '4876f9ca0d91362fae6cd4f9cde5d0044295682e')

        token = Token.select().where(Token.token == content['token']).get()
        token.delete_instance()

    def test_create_with_token_collision(self) -> None:
        device = Device.create(apns_token='apnstoken')
        token = Token.create(
            device=device,
            token='4876f9ca0d91362fae6cd4f9cde5d0044295682e',
            scope=Token.ALL_SCOPE,
        )

        headers = {
            'AUTHORIZATION': 'token e4763f7165d73e2636cca9e',
            'Content-Type': 'application/json',
        }
        response = self.client.post(
            '/authorisations',
            headers=headers,
            body=json.dumps(
                {'token': '4876f9ca0d91362fae6cd4f9cde5d0044295682e'}
            ).encode('utf-8'),
        )
        self.assertEqual(response.status_code, 403)

        token.delete_instance()
        device.delete_instance()

    def test_returns_200_when_re_registering(self) -> None:
        headers = {
            'AUTHORIZATION': 'token e4763f7165d73e2636cca9e',
            'Content-Type': 'application/json',
        }
        response = self.client.post(
            '/authorisations',
            headers=headers,
            body=json.dumps(
                {'token': '4876f9ca0d91362fae6cd4f9cde5d0044295682e'}
            ).encode('utf-8'),
        )
        self.assertEqual(response.status_code, 201)
        response = self.client.post(
            '/authorisations',
            headers=headers,
            body=json.dumps(
                {'token': '4876f9ca0d91362fae6cd4f9cde5d0044295682e'}
            ).encode('utf-8'),
        )

        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)
        self.assertTrue('url' in content)
        self.assertTrue('token' in content)
        self.assertTrue('token_last_eight' in content)
        # self.assertEqual(len('token_last_eight'), 8)
        self.assertTrue('scopes' in content)
        self.assertEqual(content['token'], '4876f9ca0d91362fae6cd4f9cde5d0044295682e')

        token = Token.select().where(Token.token == content['token']).get()
        token.delete_instance()


class AuthorisationDetailViewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = Client(app)

        self.device = Device.create(
            apns_token='ec1752bd70320e4763f7165d73e2636cca9e25cf'
        )
        self.token = Token.create(
            device=self.device, token='e4763f7165d73e2636cca9e', scope=Token.ALL_SCOPE
        )

    def tearDown(self) -> None:
        if self.token:
            self.token.delete_instance()

        self.device.delete_instance()

    def test_get(self) -> None:
        headers = {'AUTHORIZATION': 'token e4763f7165d73e2636cca9e'}
        response = self.client.get('/authorisations/636cca9e', {}, headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {
                'url': '/authorisations/636cca9e',
                'scopes': ['all'],
                'token_last_eight': '636cca9e',
            },
        )

    def test_delete(self) -> None:
        headers = {'AUTHORIZATION': 'token e4763f7165d73e2636cca9e'}
        response = self.client.delete('/authorisations/636cca9e', {}, headers)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(Token.select().count(), 0)

        self.token = None
