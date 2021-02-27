from palaverapi.models import Device, Token
from palaverapi.views.push import queue


def test_push(client):
    enqueued = []

    def enqueue(*args):
        enqueued.append(args)

    queue.enqueue = enqueue

    device = Device.create(apns_token='ec1752bd70320e4763f7165d73e2636cca9e25cf')
    token = Token.create(device=device, token='valid', scope=Token.ALL_SCOPE)

    headers = {'AUTHORIZATION': 'token valid', 'Content-Type': 'application/json'}
    response = client.post('/1/push', headers=headers, body=b'{}')
    assert response.status_code == 202
    assert len(enqueued) == 1

    token.delete_instance()
    device.delete_instance()


def test_push_without_authorization(client):
    response = client.post('/1/push')

    assert response.status_code == 401
    assert response.content_type == 'application/problem+json'


def test_push_with_invalid_authorization(client):
    response = client.post(
        '/1/push',
        headers={
            'Authorization': 'Bearer x',
        },
    )

    assert response.status_code == 401
    assert response.content_type == 'application/problem+json'
