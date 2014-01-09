import unittest
from rivr.tests import TestClient

from palaverapi.views import router


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(router)

    def test_status(self):
        assert self.client.get('/').status_code is 204

