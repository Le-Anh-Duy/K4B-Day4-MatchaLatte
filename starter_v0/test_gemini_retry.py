"""Self-check for the 429 backoff in GeminiProvider.

Run: python test_gemini_retry.py
Retries only on rate-limit errors, re-raises everything else, gives up after 5 tries.
"""
from __future__ import annotations

import os
import sys
import time
import types

from providers import gemini_provider
from providers.gemini_provider import GeminiProvider


def install_fake_genai(errors: list[Exception]) -> dict[str, int]:
    """Replace google.genai with a stub whose generate_content raises `errors` in order."""
    seen = {"calls": 0}

    class FakeModels:
        def generate_content(self, **kwargs):
            seen["calls"] += 1
            if errors:
                raise errors.pop(0)
            return types.SimpleNamespace(candidates=[], function_calls=[])

    class FakeClient:
        def __init__(self, api_key=None):
            self.models = FakeModels()

    fake_genai = types.ModuleType("google.genai")
    fake_genai.Client = FakeClient
    fake_types = types.ModuleType("google.genai.types")
    fake_types.Tool = lambda **kw: kw
    fake_types.GenerateContentConfig = lambda **kw: kw

    google_pkg = sys.modules.get("google") or types.ModuleType("google")
    google_pkg.genai = fake_genai
    sys.modules["google"] = google_pkg
    sys.modules["google.genai"] = fake_genai
    sys.modules["google.genai.types"] = fake_types
    return seen


def rate_limit_error(retry_delay: int | None = None) -> Exception:
    detail = f", 'retryDelay': '{retry_delay}s'" if retry_delay is not None else ""
    return RuntimeError(
        "429 RESOURCE_EXHAUSTED. {'error': {'code': 429, "
        f"'message': 'Resource has been exhausted (e.g. check quota).'{detail}}}}}"
    )


def complete(provider: GeminiProvider):
    return provider.complete([{"role": "user", "content": "ping"}], tools=None)


def main() -> None:
    os.environ.setdefault("GEMINI_API_KEY", "test-key")
    slept: list[int] = []
    gemini_provider.time = types.SimpleNamespace(sleep=slept.append)  # keep the check instant
    provider = GeminiProvider()

    seen = install_fake_genai([rate_limit_error(), rate_limit_error()])
    complete(provider)
    assert seen["calls"] == 3, f"expected 2 retries then success, got {seen['calls']} calls"

    seen = install_fake_genai([ValueError("bad request")])
    try:
        complete(provider)
    except ValueError:
        pass
    else:
        raise AssertionError("non-429 error must propagate, not be retried")
    assert seen["calls"] == 1, f"non-429 must not retry, got {seen['calls']} calls"

    seen = install_fake_genai([rate_limit_error() for _ in range(9)])
    try:
        complete(provider)
    except RuntimeError:
        pass
    else:
        raise AssertionError("persistent 429 must eventually raise")
    assert seen["calls"] == 8, f"expected 8 attempts before giving up, got {seen['calls']}"

    slept.clear()
    install_fake_genai([rate_limit_error(retry_delay=7)])
    complete(provider)
    assert slept == [8], f"expected the API retryDelay of 7s plus 1s margin, slept {slept}"

    print("ok: retries 429, honours retryDelay, propagates other errors, gives up after 8 attempts")


if __name__ == "__main__":
    main()
