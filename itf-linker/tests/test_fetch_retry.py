"""The daily archive's fetch must survive a flaky minute at the MPC.

The ITF is regenerated continuously and the MPC serves only the current version, so a
run that dies on one transient error costs a day of delta history that cannot be
recovered afterwards. Scheduled runs failed on 2026-07-30, 08-01, 08-05 and 08-06 while
succeeding on the days between; the fetch had no retry at all.

No network is touched here -- ``requests.get`` is replaced and ``sleep`` is injected.
"""

from __future__ import annotations

import pytest
import requests

from itf_linker.ingest import fetch


class _Resp:
    def __init__(self, status: int) -> None:
        self.status_code = status
        self.closed = False

    def close(self) -> None:
        self.closed = True

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}", response=self)


def _patch(monkeypatch, outcomes):
    """Serve ``outcomes`` in order; each is a status int or an exception to raise."""
    calls = []

    def fake_get(url, **kw):
        calls.append(url)
        item = outcomes[len(calls) - 1]
        if isinstance(item, Exception):
            raise item
        return _Resp(item)

    monkeypatch.setattr(fetch.requests, "get", fake_get)
    return calls


def test_succeeds_without_retrying_when_the_first_attempt_works(monkeypatch):
    calls = _patch(monkeypatch, [200])
    resp = fetch._get("http://example/itf", sleep=lambda _: None)
    assert resp.status_code == 200
    assert len(calls) == 1


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_retries_transient_status_and_then_succeeds(monkeypatch, status):
    calls = _patch(monkeypatch, [status, 200])
    slept: list[float] = []
    resp = fetch._get("http://example/itf", sleep=slept.append)
    assert resp.status_code == 200
    assert len(calls) == 2
    assert slept == [fetch.FETCH_BACKOFF_S]


def test_retries_connection_error_and_timeout(monkeypatch):
    calls = _patch(
        monkeypatch,
        [requests.ConnectionError("reset"), requests.Timeout("slow"), 200],
    )
    slept: list[float] = []
    assert fetch._get("http://example/itf", sleep=slept.append).status_code == 200
    assert len(calls) == 3
    # Exponential, not constant -- a server that is briefly overloaded should not be
    # hit again at the same cadence.
    assert slept == [fetch.FETCH_BACKOFF_S, fetch.FETCH_BACKOFF_S * 2]


def test_does_not_retry_a_client_error(monkeypatch):
    """404 means the request is wrong; repeating it only adds load."""
    calls = _patch(monkeypatch, [404, 200])
    with pytest.raises(requests.HTTPError):
        fetch._get("http://example/itf", sleep=lambda _: None)
    assert len(calls) == 1


def test_gives_up_after_the_attempt_budget_and_raises(monkeypatch):
    """A real outage must still surface as an error, not a silently empty snapshot."""
    calls = _patch(monkeypatch, [requests.ConnectionError("down")] * fetch.FETCH_ATTEMPTS)
    with pytest.raises(requests.ConnectionError):
        fetch._get("http://example/itf", sleep=lambda _: None)
    assert len(calls) == fetch.FETCH_ATTEMPTS


def test_transient_status_exhausts_budget_and_raises(monkeypatch):
    calls = _patch(monkeypatch, [503] * fetch.FETCH_ATTEMPTS)
    with pytest.raises(requests.HTTPError):
        fetch._get("http://example/itf", sleep=lambda _: None)
    assert len(calls) == fetch.FETCH_ATTEMPTS
