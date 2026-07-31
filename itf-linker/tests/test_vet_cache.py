"""The politeness layer is the part that can get this project banned, so it is tested hard.

Every assertion here is about *not* doing something: not re-requesting what is on disk, not
requesting faster than the floor, not caching an outage, not retrying forever, and not
continuing to hammer a service that has started failing.
"""

from __future__ import annotations

import pytest

from itf_linker.vet.cache import CachedSession, ServiceUnavailable

URL = "https://example.invalid/api"


class FakeResponse:
    def __init__(self, status: int, text: str = "{}", headers: dict | None = None) -> None:
        self.status_code = status
        self.text = text
        self.url = URL
        self.headers = headers or {}


class FakeHTTP:
    """Stands in for ``requests.Session``; records every call and replays a script."""

    def __init__(self, script: list) -> None:
        self.script = list(script)
        self.calls: list[dict] = []
        self.headers: dict[str, str] = {"User-Agent": "test"}

    def get(self, url, params=None, timeout=None, allow_redirects=True):
        self.calls.append({"url": url, "params": dict(params or {})})
        item = self.script.pop(0) if self.script else FakeResponse(200)
        if isinstance(item, Exception):
            raise item
        return item


def make(tmp_path, script, **kwargs):
    slept: list[float] = []
    session = CachedSession(tmp_path / "cache", sleeper=slept.append, **kwargs)
    fake = FakeHTTP(script)
    session._session = fake
    return session, fake, slept


def test_a_cached_response_costs_no_request(tmp_path):
    session, fake, _ = make(tmp_path, [FakeResponse(200, '{"ok":1}')])
    first = session.get("svc", URL, {"a": 1})
    second = session.get("svc", URL, {"a": 1})
    assert first.text == second.text == '{"ok":1}'
    assert first.from_cache is False and second.from_cache is True
    assert len(fake.calls) == 1
    assert session.stats["svc"]["cache_hits"] == 1


def test_different_parameters_are_different_cache_entries(tmp_path):
    session, fake, _ = make(tmp_path, [FakeResponse(200, "A"), FakeResponse(200, "B")])
    assert session.get("svc", URL, {"a": 1}).text == "A"
    assert session.get("svc", URL, {"a": 2}).text == "B"
    assert len(fake.calls) == 2


def test_requests_to_one_host_are_spaced_by_the_floor(tmp_path):
    session, _, slept = make(
        tmp_path, [FakeResponse(200, "A"), FakeResponse(200, "B")], min_interval_s=2.5
    )
    session.get("svc", URL, {"a": 1})
    session.get("svc", URL, {"a": 2})
    # The first request has nothing to wait for; the second must wait almost the full floor.
    assert slept and max(slept) > 2.0
    assert max(slept) <= 2.5


def test_an_outage_is_never_cached(tmp_path):
    """A 504 is a fact about a moment. Caching it would make it permanent."""
    session, fake, _ = make(tmp_path, [FakeResponse(504), FakeResponse(200, "good")])
    assert session.get("svc", URL, {"a": 1}).text == "good"
    assert len(fake.calls) == 2
    # The successful body is what landed on disk, and it is now free.
    assert session.get("svc", URL, {"a": 1}).from_cache is True
    assert len(fake.calls) == 2


def test_retryable_status_backs_off_before_retrying(tmp_path):
    session, fake, slept = make(
        tmp_path, [FakeResponse(503), FakeResponse(503), FakeResponse(200, "ok")],
        min_interval_s=0.0, backoff_base_s=4.0,
    )
    assert session.get("svc", URL, {}).text == "ok"
    assert len(fake.calls) == 3
    assert session.stats["svc"]["retries"] == 2
    # Exponential: the second backoff must exceed the first.
    backoffs = [s for s in slept if s >= 4.0]
    assert len(backoffs) == 2 and backoffs[1] > backoffs[0]


def test_retry_after_header_is_honoured(tmp_path):
    session, _, slept = make(
        tmp_path,
        [FakeResponse(429, headers={"Retry-After": "90"}), FakeResponse(200, "ok")],
        min_interval_s=0.0, backoff_base_s=1.0,
    )
    session.get("svc", URL, {})
    assert max(slept) >= 90.0


def test_a_non_retryable_status_fails_at_once(tmp_path):
    session, fake, _ = make(tmp_path, [FakeResponse(404)], min_interval_s=0.0)
    with pytest.raises(ServiceUnavailable, match="404"):
        session.get("svc", URL, {})
    assert len(fake.calls) == 1


def test_a_failing_service_is_switched_off_rather_than_hammered(tmp_path):
    """The circuit breaker: after the budget, stop calling. Do not route around it."""
    script = [FakeResponse(503)] * 40
    session, fake, _ = make(
        tmp_path, script, min_interval_s=0.0, backoff_base_s=0.0,
        max_retries=0, failure_budget=3,
    )
    for i in range(3):
        with pytest.raises(ServiceUnavailable):
            session.get("svc", URL, {"n": i})
    assert "svc" in session.disabled
    calls_before = len(fake.calls)
    with pytest.raises(ServiceUnavailable, match="consecutive failures"):
        session.get("svc", URL, {"n": 99})
    assert len(fake.calls) == calls_before, "a disabled service must not be contacted again"


def test_a_success_resets_the_failure_count(tmp_path):
    session, _, _ = make(
        tmp_path, [FakeResponse(503), FakeResponse(200, "ok"), FakeResponse(503)],
        min_interval_s=0.0, backoff_base_s=0.0, max_retries=0, failure_budget=2,
    )
    with pytest.raises(ServiceUnavailable):
        session.get("svc", URL, {"n": 1})
    session.get("svc", URL, {"n": 2})
    with pytest.raises(ServiceUnavailable):
        session.get("svc", URL, {"n": 3})
    assert "svc" not in session.disabled


def test_a_transport_exception_is_treated_as_a_failure(tmp_path):
    import requests

    session, _, _ = make(
        tmp_path, [requests.Timeout("read timed out"), FakeResponse(200, "ok")],
        min_interval_s=0.0, backoff_base_s=0.0,
    )
    assert session.get("svc", URL, {}).text == "ok"


def test_max_retries_can_be_overridden_per_call(tmp_path):
    """SBIDENT uses this: a four-minute timeout is not a transient blip."""
    session, fake, _ = make(
        tmp_path, [FakeResponse(504)] * 10, min_interval_s=0.0, backoff_base_s=0.0
    )
    with pytest.raises(ServiceUnavailable):
        session.get("svc", URL, {}, max_retries=0)
    assert len(fake.calls) == 1


def test_offline_mode_serves_the_cache_and_refuses_the_network(tmp_path):
    session, fake, _ = make(tmp_path, [FakeResponse(200, "cached")])
    session.get("svc", URL, {"a": 1})
    session.offline = True
    assert session.get("svc", URL, {"a": 1}).text == "cached"
    with pytest.raises(ServiceUnavailable, match="offline"):
        session.get("svc", URL, {"a": 2})
    assert len(fake.calls) == 1


def test_summary_reports_the_politeness_settings(tmp_path):
    session, _, _ = make(tmp_path, [FakeResponse(200)], min_interval_s=1.5)
    session.get("svc", URL, {})
    summary = session.summary()
    assert summary["min_interval_s"] == 1.5
    assert summary["per_service"]["svc"]["requests"] == 1
    assert "User-Agent" not in summary  # the value, not the header name
    assert summary["user_agent"]
