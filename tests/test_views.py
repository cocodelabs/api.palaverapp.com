import json
import unittest

from rivr.test import Client

from palaverapi import app
from palaverapi.models import Device, Token


class ViewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = Client(app)

    def test_status(self) -> None:
        assert self.client.get('/').status_code == 204

    def test_register(self) -> None:
        response = self.client.post(
            '/1/devices',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({'device_token': 'test_token'}).encode('utf-8'),
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(
            response.content,
            '{"device_token": "test_token", "push_token": "ec1752bd70320e4763f7165d73e2636cca9e25cf"}',
        )

        device = Device.get(apns_token='test_token')
        assert device

        push_token = (
            Token.select()
            .where(
                Token.device == device,
                Token.token == 'ec1752bd70320e4763f7165d73e2636cca9e25cf',
            )
            .get()
        )
        token = (
            Token.select()
            .where(Token.device == device, Token.token == 'test_token')
            .get()
        )

        token.delete_instance()
        push_token.delete_instance()
        device.delete_instance()

    def test_returns_200_when_re_registering(self) -> None:
        response = self.client.post(
            '/1/devices',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({'device_token': 'test_token'}).encode('utf-8'),
        )
        response = self.client.post(
            '/1/devices',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({'device_token': 'test_token'}).encode('utf-8'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(
            response.content,
            '{"device_token": "test_token", "push_token": "ec1752bd70320e4763f7165d73e2636cca9e25cf"}',
        )

        device = Device.get(apns_token='test_token')
        assert device

        push_token = (
            Token.select()
            .where(
                Token.device == device,
                Token.token == 'ec1752bd70320e4763f7165d73e2636cca9e25cf',
            )
            .get()
        )
        token = (
            Token.select()
            .where(Token.device == device, Token.token == 'test_token')
            .get()
        )

        push_token.delete_instance()
        token.delete_instance()
        device.delete_instance()
