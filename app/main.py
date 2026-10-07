"""HTTP API. Run with: uvicorn app.main:create_app --factory"""

import logging
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config
from .dreams import DreamMatcher, MatcherUnavailable, load_entries

log = logging.getLogger(__name__)


class DreamRequest(BaseModel):
    text: str = Field(min_length=3)


class DreamMatchOut(BaseModel):
    id: str
    dream: str
    interpretation: str
    source: str


class DreamResponse(BaseModel):
    status: str  # "matched" | "not_found"
    message: str
    matches: list[DreamMatchOut]


class RateLimiter:
    """In-memory sliding window per client. Single-process only; use Redis if you scale out."""

    def __init__(self, calls: int, window_s: int):
        self.calls, self.window_s = calls, window_s
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window_s:
            hits.popleft()
        if len(hits) >= self.calls:
            return False
        hits.append(now)
        return True


def create_app(
    matcher: DreamMatcher | None = None, settings: config.Settings | None = None
) -> FastAPI:
    settings = settings or config.load_settings()
    if matcher is None:
        entries = load_entries(settings.dreams_path)
        log.info("loaded %d dream entries from %s", len(entries), settings.dreams_path)
        matcher = DreamMatcher(
            entries,
            model=settings.model,
            shortlist_size=settings.shortlist_size,
            min_score=settings.min_score,
        )
    limiter = RateLimiter(settings.rate_limit_calls, settings.rate_limit_window_s)

    app = FastAPI(title="Dream book API")
    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware, allow_origins=settings.allowed_origins, allow_methods=["POST"],
            allow_headers=["content-type"],
        )

    def client_key(request: Request) -> str:
        if settings.trust_forwarded_for:
            forwarded = request.headers.get("x-forwarded-for", "")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    @app.get("/health")
    def health():
        return {"ok": True, "entries": len(matcher.entries)}

    @app.post("/api/dream", response_model=DreamResponse)
    def dream(body: DreamRequest, request: Request):
        # Dream text is private: it is never logged.
        if len(body.text) > settings.max_input_chars:
            raise HTTPException(422, f"সর্বোচ্চ {settings.max_input_chars} অক্ষর লিখুন।")
        if not limiter.allow(client_key(request)):
            raise HTTPException(429, "অনেকবার চেষ্টা করা হয়েছে। কিছুক্ষণ পরে আবার চেষ্টা করুন।")
        try:
            result = matcher.match(body.text)
        except MatcherUnavailable:
            raise HTTPException(503, config.UNAVAILABLE_MESSAGE)
        if not result.found:
            return DreamResponse(status="not_found", message=config.NOT_FOUND_MESSAGE, matches=[])
        return DreamResponse(
            status="matched",
            message=config.DISCLAIMER,
            matches=[
                DreamMatchOut(id=e.id, dream=e.dream, interpretation=e.interpretation, source=e.source)
                for e in result.matches
            ],
        )

    app.mount("/", StaticFiles(directory=config.ROOT / "static", html=True), name="static")
    return app
