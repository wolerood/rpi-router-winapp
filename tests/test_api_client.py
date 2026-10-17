import unittest
import sys
import types

if "requests" not in sys.modules:
    requests_stub = types.ModuleType("requests")
    requests_stub.RequestException = Exception
    requests_stub.Session = object
    sys.modules["requests"] = requests_stub

from api_client import ApiClient


class FakeResponse:
    ok = True

    @staticmethod
    def json():
        return {"ok": True}


class FakeSession:
    def __init__(self):
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return FakeResponse()


class ApiClientTokenTests(unittest.TestCase):
    def setUp(self):
        self.client = ApiClient(
            "http://router:8080",
            api_token="secret-token",
        )
        self.client.session = FakeSession()

    def test_write_request_includes_token(self):
        self.client.create_user("Test")

        method, _, kwargs = self.client.session.calls[0]
        self.assertEqual(method, "POST")
        self.assertEqual(kwargs["headers"]["X-API-Token"], "secret-token")

    def test_read_request_does_not_include_token(self):
        self.client.get_users()

        method, _, kwargs = self.client.session.calls[0]
        self.assertEqual(method, "GET")
        self.assertNotIn("headers", kwargs)


if __name__ == "__main__":
    unittest.main()
