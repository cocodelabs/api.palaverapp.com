import json
import unittest

from rivr.test import Client

from palaverapi import app
from palaverapi.models import Device, Token


class DeviceDetailViewTests(unittest.TestCase):
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

    def test_get_device(self) -> None:
        headers = {'AUTHORIZATION': 'token e4763f7165d73e2636cca9e'}
        response = self.client.http('GET', '/device', {}, headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')

        device_detail = json.loads(response.content)
        assert sorted(device_detail.keys()) == ['apns_token', 'created_at']
        assert device_detail['apns_token'] == 'ec1752bd70320e4763f7165d73e2636cca9e25cf'
        assert device_detail['created_at'].endswith('Z')

    def test_get_device_without_created_at(self) -> None:
        self.device.created_at = None
        self.device.save()

        headers = {'AUTHORIZATION': 'token e4763f7165d73e2636cca9e'}
        response = self.client.http('GET', '/device', {}, headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')

        device_detail = json.loads(response.content)
        assert sorted(device_detail.keys()) == ['apns_token']
        assert device_detail['apns_token'] == 'ec1752bd70320e4763f7165d73e2636cca9e25cf'

    def test_update_apns_token(self) -> None:
        headers = {
            'AUTHORIZATION': 'token e4763f7165d73e2636cca9e',
            'Content-Type': 'application/json',
        }
        response = self.client.http(
            'PATCH',
            '/device',
            headers=headers,
            body=json.dumps({'apns_token': 'new_token'}).encode('utf-8'),
        )

        self.assertEqual(response.status_code, 204)

        device = Token.get(token=self.token.token).device
        self.assertEqual(device.apns_token, 'new_token')

    def test_delete_device(self) -> None:
        headers = {'AUTHORIZATION': 'token e4763f7165d73e2636cca9e'}
        response = self.client.http('DELETE', '/device', headers=headers)

        self.assertEqual(response.status_code, 204)

        self.assertEqual(Token.select().count(), 0)
        self.assertEqual(Device.select().count(), 0)

    def test_delete_device_push_token(self) -> None:
        self.token.scope = Token.PUSH_SCOPE
        self.token.save()

        headers = {'AUTHORIZATION': 'token e4763f7165d73e2636cca9e'}
        response = self.client.http('DELETE', '/device', headers=headers)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers['Content-Type'], 'application/problem+json')
