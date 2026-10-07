import json
from types import SimpleNamespace

import pytest

from app.config import ROOT
from app.dreams import load_entries


class FakeClient:
    """Stands in for anthropic.Anthropic; records calls, returns a canned structured output."""

    def __init__(self, payload=None, stop_reason="end_turn", raw_text=None, error=None):
        self.calls = []
        self._payload, self._stop, self._raw, self._error = payload, stop_reason, raw_text, error
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        text = self._raw if self._raw is not None else json.dumps(self._payload)
        return SimpleNamespace(
            stop_reason=self._stop,
            usage=SimpleNamespace(input_tokens=100, output_tokens=20),
            content=[SimpleNamespace(type="text", text=text)],
        )


@pytest.fixture
def entries():
    return load_entries(ROOT / "data" / "dreams.sample.json")
