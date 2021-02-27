def test_health(client):
    response = client.get('/health')

    assert response.status_code == 200
    assert response.content_type == 'application/health+json'
    assert response.content == '{"status": "pass"}'
