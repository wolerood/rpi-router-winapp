import sys
import types
import unittest

try:
    import requests  # noqa: F401
except ModuleNotFoundError:
    requests_stub = types.ModuleType("requests")
    requests_stub.RequestException = Exception

    class StubSession:
        pass

    requests_stub.Session = StubSession
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

    def test_real_session_ignores_system_proxy_settings(self):
        client = ApiClient("http://192.168.0.2:8080")

        self.assertFalse(client.session.trust_env)

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

    def test_create_device_assigns_one_user(self):
        self.client.create_device(7, "aa:bb:cc:dd:ee:ff", "Phone")

        method, url, kwargs = self.client.session.calls[0]
        self.assertEqual(method, "POST")
        self.assertEqual(url, "http://router:8080/devices")
        self.assertEqual(
            kwargs["json"],
            {
                "user_id": 7,
                "mac": "aa:bb:cc:dd:ee:ff",
                "name": "Phone",
            },
        )

    def test_update_device_reassigns_user(self):
        self.client.update_device(12, user_id=9)

        method, url, kwargs = self.client.session.calls[0]
        self.assertEqual(method, "PATCH")
        self.assertEqual(url, "http://router:8080/devices/12")
        self.assertEqual(kwargs["json"], {"user_id": 9})

    def test_create_schedule_sends_iso_weekday_and_times(self):
        self.client.create_schedule(7, 1, "08:30", "20:15")

        method, url, kwargs = self.client.session.calls[0]
        self.assertEqual(method, "POST")
        self.assertEqual(url, "http://router:8080/schedules")
        self.assertEqual(
            kwargs["json"],
            {
                "user_id": 7,
                "weekday": 1,
                "start": "08:30",
                "end": "20:15",
            },
        )

    def test_update_schedule_sends_all_edited_fields(self):
        self.client.update_schedule(
            15,
            user_id=9,
            weekday=7,
            start="10:00",
            end="22:00",
        )

        method, url, kwargs = self.client.session.calls[0]
        self.assertEqual(method, "PATCH")
        self.assertEqual(url, "http://router:8080/schedules/15")
        self.assertEqual(
            kwargs["json"],
            {
                "user_id": 9,
                "weekday": 7,
                "start": "10:00",
                "end": "22:00",
            },
        )

    def test_delete_schedule_uses_selected_schedule_id(self):
        self.client.delete_schedule(15)

        method, url, kwargs = self.client.session.calls[0]
        self.assertEqual(method, "DELETE")
        self.assertEqual(url, "http://router:8080/schedules/15")
        self.assertEqual(kwargs["headers"]["X-API-Token"], "secret-token")


if __name__ == "__main__":
    unittest.main()
