from typing import Iterator, List, Tuple, Generator

import pytest
from rivr.test import Client

from palaverapi.models import Device, Token
from palaverapi.utils import create_payload
from palaverapi.views.push import queue


@pytest.fixture
def token() -> Iterator[Token]:
    device = Device.create(apns_token='ec1752bd70320e4763f7165d73e2636cca9e25cf')
    token = Token.create(device=device, token='valid', scope=Token.ALL_SCOPE)

    yield token

    token.delete_instance()
    device.delete_instance()


@pytest.fixture
def enqueued() -> List[Tuple]:
    enqueued = []

    def enqueue(*args):
        enqueued.append(args)

    queue.enqueue = enqueue
    return enqueued


def test_push(client: Client, token: Token, enqueued: List[Tuple]) -> None:
    response = client.post(
        '/1/push',
        headers={
            'Authorization': 'Bearer valid',
            'Content-Type': 'application/json',
        },
        body=b'{"sender": "doe", "message": "Hello World"}',
    )

    assert response.status_code == 202

    assert len(enqueued) == 1
    assert enqueued[0][1] == 'ec1752bd70320e4763f7165d73e2636cca9e25cf'

    payload = create_payload(*(enqueued[0][2:]))

    assert payload.alert['title'] == 'doe'
    assert payload.alert['body'] == 'Hello World'
    assert 'subtitle' not in payload.alert
    assert payload.badge == 1
    assert payload.sound == 'default'


def test_push_channel_message(client: Client, token: Token, enqueued: List[Tuple]) -> None:
    response = client.post(
        '/1/push',
        headers={
            'Authorization': 'Bearer valid',
            'Content-Type': 'application/json',
        },
        body=b'{"sender": "doe", "message": "Hello World", "channel": "#example"}',
    )

    assert response.status_code == 202

    assert len(enqueued) == 1
    assert enqueued[0][1] == 'ec1752bd70320e4763f7165d73e2636cca9e25cf'

    payload = create_payload(*(enqueued[0][2:]))

    assert payload.alert['title'] == 'doe'
    assert payload.alert['subtitle'] == '#example'
    assert payload.alert['body'] == 'Hello World'
    assert payload.badge == 1
    assert payload.sound == 'default'


def test_push_private_message(client: Client, token: Token, enqueued: List[Tuple]) -> None:
    response = client.post(
        '/1/push',
        headers={
            'Authorization': 'Bearer valid',
            'Content-Type': 'application/json',
        },
        body=b'{"private": true}',
    )

    assert response.status_code == 202

    assert len(enqueued) == 1
    assert enqueued[0][1] == 'ec1752bd70320e4763f7165d73e2636cca9e25cf'

    payload = create_payload(*(enqueued[0][2:]))

    assert 'title' not in payload.alert
    assert 'subtitle' not in payload.alert
    assert payload.alert['body'] == 'Message'
    assert payload.badge == 1
    assert payload.sound == 'default'


def test_push_invalid_json(client: Client, token: Token, enqueued: List[Tuple]) -> None:
    response = client.post(
        '/1/push',
        headers={
            'Authorization': 'Bearer valid',
            'Content-Type': 'application/json',
        },
        body=b'{"sender: "doe", "message": "Hello World"}',
    )

    assert response.status_code == 400
    assert response.content == '{"title": "Invalid request body"}'


def test_push_unsupported_content_type(client: Client, token: Token, enqueued: List[Tuple]) -> None:
    response = client.post(
        '/1/push',
        headers={
            'Authorization': 'Bearer valid',
            'Content-Type': 'application/yaml',
        },
        body=b'message: Hello World',
    )

    assert response.status_code == 415
    assert response.content == '{"title": "Unsupported Media Type"}'


def test_push_without_authorization(client: Client) -> None:
    response = client.post('/1/push')

    assert response.status_code == 401
    assert response.content_type == 'application/problem+json'


def test_push_with_invalid_authorization(client: Client) -> None:
    response = client.post(
        '/1/push',
        headers={
            'Authorization': 'Bearer x',
        },
    )

    assert response.status_code == 401
    assert response.content_type == 'application/problem+json'
