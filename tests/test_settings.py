import sys
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from settings import ClientSettings


class FakeSettings:
    def __init__(self, values=None):
        self.values = values if values is not None else {}
        self.synced = False

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value

    def sync(self):
        self.synced = True


class ClientSettingsTests(unittest.TestCase):
    def test_connection_settings_are_persisted(self):
        stored_values = {}
        backend = FakeSettings(stored_values)
        writer = ClientSettings(backend)

        writer.save_connection(
            "  http://192.168.1.2:8080/  ",
            "  secret-token  ",
        )

        reader = ClientSettings(FakeSettings(stored_values))
        self.assertEqual(
            reader.api_url(),
            "http://192.168.1.2:8080/",
        )
        self.assertEqual(reader.api_token(), "secret-token")
        self.assertTrue(backend.synced)


if __name__ == "__main__":
    unittest.main()
