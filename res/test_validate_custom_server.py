import base64
import unittest

from validate_custom_server import validate


class ValidateCustomServerTests(unittest.TestCase):
    def setUp(self):
        self.values = {
            "RENDEZVOUS_SERVER": "rd.example.com:21116",
            "RS_PUB_KEY": base64.b64encode(bytes(range(32))).decode(),
        }

    def test_valid_server_and_optional_settings(self):
        validate(self.values)
        validate(dict(self.values, RELAY_SERVER="relay.example.com:21117", API_SERVER="https://api.example.com"))

    def test_missing_or_invalid_public_key(self):
        for key in ("", "not-base64", base64.b64encode(b"short").decode()):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(dict(self.values, RS_PUB_KEY=key))

    def test_invalid_server_addresses(self):
        for host in ("", " rd.example.com", "https://rd.example.com", "rd.example.com/path", "user:pass@rd.example.com", "rd.example.com:99999"):
            with self.subTest(host=host), self.assertRaises(ValueError):
                validate(dict(self.values, RENDEZVOUS_SERVER=host))


if __name__ == "__main__":
    unittest.main()
