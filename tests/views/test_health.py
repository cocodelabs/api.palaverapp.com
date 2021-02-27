from rivr.test import Client


def test_health(client: Client) -> None:
    response = client.get('/health')

    assert response.status_code == 200
    assert response.content_type == 'application/health+json'
    assert response.content == '{"status": "pass"}'
