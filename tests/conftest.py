import pytest
from rivr.test import Client

from palaverapi import app


@pytest.fixture
def client() -> Client:
    return Client(app)
