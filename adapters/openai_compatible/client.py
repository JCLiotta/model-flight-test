"""Small dependency-free client for OpenAI-compatible model endpoints.

This transport layer intentionally does not implement fallback routing or write
files. Callers own run-directory isolation and deterministic validation.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Iterable, Optional


class OpenAICompatibleHTTPError(RuntimeError):
    """HTTP failure that preserves the status and response body for attribution."""

    def __init__(self, status: int, body: str):
        super().__init__(f"OpenAI-compatible endpoint returned HTTP {status}: {body}")
        self.status = status
        self.body = body


class OpenAICompatibleClient:
    def __init__(self, base_url: str, model: str, api_key: Optional[str] = None, timeout: int = 300):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def _get(self, path: str) -> Dict[str, Any]:
        request = urllib.request.Request(self.base_url + path)
        if self.api_key:
            request.add_header("Authorization", "Bearer " + self.api_key)
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def list_models(self) -> Dict[str, Any]:
        return self._get("/models")

    def health(self) -> bool:
        with urllib.request.urlopen(self.base_url.rsplit("/v1", 1)[0] + "/health", timeout=15) as response:
            return response.status == 200

    def chat(self, messages: Iterable[Dict[str, Any]], max_tokens: int = 4096, **generation: Any) -> Dict[str, Any]:
        payload = {"model": self.model, "messages": list(messages), "max_tokens": max_tokens}
        payload.update(generation)
        request = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        if self.api_key:
            request.add_header("Authorization", "Bearer " + self.api_key)
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise OpenAICompatibleHTTPError(exc.code, body) from exc
        result["flight_latency_ms"] = round((time.monotonic() - started) * 1000, 1)
        returned = result.get("model")
        result["flight_model_match"] = returned == self.model
        return result
