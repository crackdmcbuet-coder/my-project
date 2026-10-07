from fastapi.testclient import TestClient

from app import config
from app.dreams import DreamMatcher
from app.main import create_app

from .conftest import FakeClient

SNAKE = "স্বপ্নে দেখলাম একটা সাপ আমার দিকে আসছে"


def make_client(entries, fake, **overrides):
    settings = config.load_settings()
    settings = settings.__class__(**{**settings.__dict__, **overrides})
    matcher = DreamMatcher(entries, client=fake, model="m")
    return TestClient(create_app(matcher=matcher, settings=settings))


def test_health(entries):
    r = make_client(entries, FakeClient({"entry_ids": []})).get("/health")
    assert r.json() == {"ok": True, "entries": 5}


def test_matched(entries):
    c = make_client(entries, FakeClient({"entry_ids": ["sample-1"]}))
    body = c.post("/api/dream", json={"text": SNAKE}).json()
    assert body["status"] == "matched"
    assert body["matches"][0]["id"] == "sample-1"
    assert body["message"] == config.DISCLAIMER


def test_not_found_uses_fixed_message(entries):
    c = make_client(entries, FakeClient({"entry_ids": []}))
    body = c.post("/api/dream", json={"text": SNAKE}).json()
    assert body == {"status": "not_found", "message": config.NOT_FOUND_MESSAGE, "matches": []}


def test_too_short_or_too_long_rejected(entries):
    c = make_client(entries, FakeClient({"entry_ids": []}), max_input_chars=20)
    assert c.post("/api/dream", json={"text": "হ"}).status_code == 422
    assert c.post("/api/dream", json={"text": "সাপ " * 30}).status_code == 422


def test_model_failure_is_503_with_retry_message(entries):
    c = make_client(entries, FakeClient(stop_reason="refusal"))
    r = c.post("/api/dream", json={"text": SNAKE})
    assert r.status_code == 503 and r.json()["detail"] == config.UNAVAILABLE_MESSAGE


def test_rate_limit_per_client(entries):
    c = make_client(entries, FakeClient({"entry_ids": []}), rate_limit_calls=2)
    codes = [c.post("/api/dream", json={"text": SNAKE}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_forwarded_for_only_trusted_when_enabled(entries):
    c = make_client(entries, FakeClient({"entry_ids": []}), rate_limit_calls=1, trust_forwarded_for=True)
    first = c.post("/api/dream", json={"text": SNAKE}, headers={"x-forwarded-for": "1.1.1.1"})
    other = c.post("/api/dream", json={"text": SNAKE}, headers={"x-forwarded-for": "2.2.2.2"})
    again = c.post("/api/dream", json={"text": SNAKE}, headers={"x-forwarded-for": "1.1.1.1"})
    assert (first.status_code, other.status_code, again.status_code) == (200, 200, 429)


def test_demo_page_is_served(entries):
    r = make_client(entries, FakeClient({"entry_ids": []})).get("/")
    assert r.status_code == 200 and "স্বপ্নের ব্যাখ্যা" in r.text
