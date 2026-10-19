import io
import unittest
import urllib.error
from unittest.mock import patch

from adapters.openai_compatible.client import (
    OpenAICompatibleClient,
    OpenAICompatibleHTTPError,
)


class OpenAICompatibleClientTests(unittest.TestCase):
    def test_chat_preserves_http_error_status_and_body(self):
        body = b'{"error":{"message":"maximum context length is 262144"}}'
        error = urllib.error.HTTPError(
            "http://example.test/v1/chat/completions",
            400,
            "Bad Request",
            {},
            io.BytesIO(body),
        )
        client = OpenAICompatibleClient("http://example.test/v1", "test-model")

        with patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(OpenAICompatibleHTTPError) as raised:
                client.chat([{"role": "user", "content": "hello"}])

        self.assertEqual(raised.exception.status, 400)
        self.assertIn("maximum context length", raised.exception.body)


if __name__ == "__main__":
    unittest.main()
