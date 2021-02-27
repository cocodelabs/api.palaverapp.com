from rivr.test import Client


def test_404(client: Client) -> None:
    response = client.get('/404')
    assert response.status_code == 404
    assert response.content_type == 'application/problem+json'
    assert response.content == '{"title": "Resource Not Found"}'


def test_500(client: Client) -> None:
    response = client.get('/500')
    assert response.status_code == 500
    assert response.content_type == 'application/problem+json'
    assert response.content == '{"title": "Internal Server Error"}'
