from typing import Generator, Iterator, List, Tuple

import pytest
from rivr.test import Client

from palaverapi.models import Device, Token
from palaverapi.utils import create_payload
from palaverapi.views.push import queue


@pytest.fixture
def token() -> Iterator[Token]:
    device = Device.create(apns_token='ec1752bd70320e4763f7165d73e2636cca9e25cf')
    token = Token.create(device=device, token='valid', scope=Token.ALL_SCOPE)
    token2 = Token.create(
        device=device, token='subscription-id', scope=Token.PUSH_SCOPE
    )

    yield token

    token.delete_instance()
    token2.delete_instance()
    device.delete_instance()


@pytest.fixture
def enqueued() -> List[Tuple]:
    enqueued = []

    def enqueue(func, args, ttl=None, kwargs=None):
        enqueued.append((func, *args))

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

    assert payload['alert']['title'] == 'doe'
    assert payload['alert']['body'] == 'Hello World'
    assert 'subtitle' not in payload['alert']
    assert payload['badge'] == 1
    assert payload['sound'] == 'default'


def test_push_with_subscription_uri(
    client: Client, token: Token, enqueued: List[Tuple]
) -> None:
    response = client.post(
        '/push/subscription-id',
        headers={
            'Content-Type': 'application/json',
            'TTL': '5',
        },
        body=b'{"sender": "doe", "message": "Hello World"}',
    )

    assert response.status_code == 202

    assert len(enqueued) == 1
    assert enqueued[0][1] == 'ec1752bd70320e4763f7165d73e2636cca9e25cf'

    payload = create_payload(*(enqueued[0][2:]))

    assert payload['alert']['title'] == 'doe'
    assert payload['alert']['body'] == 'Hello World'
    assert 'subtitle' not in payload['alert']
    assert payload['badge'] == 1
    assert payload['sound'] == 'default'


def test_push_with_subscription_uri_text_irc(
    client: Client, token: Token, enqueued: List[Tuple]
) -> None:
    response = client.post(
        '/push/subscription-id',
        headers={
            'Content-Type': 'text/irc',
            'TTL': '5',
        },
        body=b':doe!~doe@example.com PRIVMSG #example :Hello World\r\n',
    )

    assert response.status_code == 202

    assert len(enqueued) == 1
    assert enqueued[0][1] == 'ec1752bd70320e4763f7165d73e2636cca9e25cf'

    payload = create_payload(*(enqueued[0][2:]))

    assert 'alert' in payload
    assert payload['alert']['title'] == 'doe'
    assert payload['alert']['subtitle'] == '#example'
    assert payload['alert']['body'] == 'Hello World'
    assert payload['badge'] == 1
    assert payload['sound'] == 'default'


def test_push_with_subscription_uri_with_low_urgency(
    client: Client, token: Token, enqueued: List[Tuple]
) -> None:
    response = client.post(
        '/push/subscription-id',
        headers={
            'Content-Type': 'application/json',
            'TTL': '5',
            'Urgency': 'low',
        },
        body=b'{"sender": "doe", "message": "Hello World"}',
    )

    assert response.status_code == 202

    assert len(enqueued) == 1
    assert enqueued[0][1] == 'ec1752bd70320e4763f7165d73e2636cca9e25cf'

    payload = create_payload(*(enqueued[0][2:]))

    assert payload['alert']['title'] == 'doe'
    assert payload['alert']['body'] == 'Hello World'
    assert 'subtitle' not in payload['alert']
    assert payload['badge'] == 1
    assert payload['sound'] == 'default'


def test_push_with_subscription_uri_with_normal_urgency(
    client: Client, token: Token, enqueued: List[Tuple]
) -> None:
    response = client.post(
        '/push/subscription-id',
        headers={
            'Content-Type': 'application/json',
            'TTL': '5',
            'Urgency': 'normal',
        },
        body=b'{"sender": "doe", "message": "Hello World"}',
    )

    assert response.status_code == 202

    assert len(enqueued) == 1
    assert enqueued[0][1] == 'ec1752bd70320e4763f7165d73e2636cca9e25cf'

    payload = create_payload(*(enqueued[0][2:]))

    assert payload['alert']['title'] == 'doe'
    assert payload['alert']['body'] == 'Hello World'
    assert 'subtitle' not in payload['alert']
    assert payload['badge'] == 1
    assert payload['sound'] == 'default'


def test_push_with_subscription_uri_with_unsupported_urgency(
    client: Client, token: Token
) -> None:
    response = client.post(
        '/push/subscription-id',
        headers={
            'Content-Type': 'application/json',
            'TTL': '5',
            'Urgency': 'very-low',
        },
        body=b'{"sender": "doe", "message": "Hello World"}',
    )

    assert response.status_code == 400


def test_push_with_subscription_uri_unsupported_media_type(
    client: Client, token: Token, enqueued: List[Tuple]
) -> None:
    response = client.post(
        '/push/subscription-id',
        headers={
            'Content-Type': 'application/yaml',
            'TTL': '5',
        },
        body=b'message: Hello World',
    )

    assert response.status_code == 415


def test_push_with_subscription_uri_not_found(client: Client, token: Token) -> None:
    response = client.post(
        '/push/unknown',
        headers={
            'Content-Type': 'application/json',
        },
        body=b'{"sender": "doe", "message": "Hello World"}',
    )

    assert response.status_code == 404


def test_push_with_subscription_uri_with_all_token(
    client: Client, token: Token
) -> None:
    response = client.post(
        '/push/valid',
        headers={
            'Content-Type': 'application/json',
            'TTL': '5',
        },
        body=b'{"sender": "doe", "message": "Hello World"}',
    )

    assert response.status_code == 404


def test_push_with_subscription_uri_without_ttl(client: Client, token: Token) -> None:
    response = client.post(
        '/push/subscription-id',
        headers={
            'Content-Type': 'application/json',
        },
        body=b'{"sender": "doe", "message": "Hello World"}',
    )

    assert response.status_code == 400


def test_push_with_subscription_uri_with_non_number_ttl(
    client: Client, token: Token
) -> None:
    response = client.post(
        '/push/subscription-id',
        headers={
            'Content-Type': 'application/json',
            'TTL': 'five',
        },
        body=b'{"sender": "doe", "message": "Hello World"}',
    )

    assert response.status_code == 400


def test_push_with_subscription_uri_with_topic(client: Client, token: Token) -> None:
    response = client.post(
        '/push/subscription-id',
        headers={
            'Content-Type': 'application/json',
            'Topic': 'test',
            'TTL': '5',
        },
        body=b'{"sender": "doe", "message": "Hello World"}',
    )

    assert response.status_code == 400


def test_push_with_subscription_uri_with_prefer_async(
    client: Client, token: Token, enqueued: List[Tuple]
) -> None:
    response = client.post(
        '/push/subscription-id',
        headers={
            'Content-Type': 'application/json',
            'Prefer': 'respond-async',
            'TTL': '5',
        },
        body=b'{"sender": "doe", "message": "Hello World"}',
    )

    assert response.status_code == 202

    assert len(enqueued) == 1
    assert enqueued[0][1] == 'ec1752bd70320e4763f7165d73e2636cca9e25cf'

    payload = create_payload(*(enqueued[0][2:]))

    assert payload['alert']['title'] == 'doe'
    assert payload['alert']['body'] == 'Hello World'
    assert 'subtitle' not in payload['alert']
    assert payload['badge'] == 1
    assert payload['sound'] == 'default'


def test_push_with_subscription_uri_with_prefer_unknown(
    client: Client, token: Token
) -> None:
    response = client.post(
        '/push/subscription-id',
        headers={
            'Content-Type': 'application/json',
            'Prefer': 'respond-sync',
            'TTL': '5',
        },
        body=b'{"sender": "doe", "message": "Hello World"}',
    )

    assert response.status_code == 400


def test_push_reset_badge(client: Client, token: Token, enqueued: List[Tuple]) -> None:
    response = client.post(
        '/1/push',
        headers={
            'Authorization': 'Bearer valid',
            'Content-Type': 'application/json',
        },
        body=b'{"badge": 0}',
    )

    assert response.status_code == 202

    assert len(enqueued) == 1
    assert enqueued[0][1] == 'ec1752bd70320e4763f7165d73e2636cca9e25cf'

    payload = create_payload(*(enqueued[0][2:]))

    assert payload['alert'] == {}
    assert payload['badge'] == 0


def test_push_channel_message(
    client: Client, token: Token, enqueued: List[Tuple]
) -> None:
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

    assert payload['alert']['title'] == 'doe'
    assert payload['alert']['subtitle'] == '#example'
    assert payload['alert']['body'] == 'Hello World'
    assert payload['badge'] == 1
    assert payload['sound'] == 'default'


def test_push_private_message(
    client: Client, token: Token, enqueued: List[Tuple]
) -> None:
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

    assert 'title' not in payload['alert']
    assert 'subtitle' not in payload['alert']
    assert payload['alert']['body'] == 'Message'
    assert payload['badge'] == 1
    assert payload['sound'] == 'default'


def test_push_empty_payload(
    client: Client, token: Token, enqueued: List[Tuple]
) -> None:
    response = client.post(
        '/1/push',
        headers={
            'Authorization': 'Bearer valid',
            'Content-Type': 'application/json',
        },
        body=b'{}',
    )

    assert response.status_code == 422
    assert len(enqueued) == 0


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


def test_push_unsupported_content_type(
    client: Client, token: Token, enqueued: List[Tuple]
) -> None:
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
