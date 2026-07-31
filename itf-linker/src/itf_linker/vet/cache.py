"""A deliberately slow, deliberately cached HTTP client for other people's servers.

MPChecker, SkyBoT, SBIDENT and SBDB are free public services run by small teams. This
module exists so that the vetting stage cannot accidentally behave like a scraper:

* **one request at a time, per host, with a floor on the interval** (default 1 s). There is
  no concurrency anywhere in :mod:`itf_linker.vet` -- not a thread pool with a semaphore, no
  concurrency at all, because a bug in a semaphore is a bug that lands on someone else's
  server.
* **every successful response is written to disk**, keyed by the exact request. A re-run of
  the whole vetting pass therefore costs zero requests, which is what makes the M2 numbers
  reproducible without asking the MPC to recompute them.
* **backoff, then stop.** Retries are exponential with jitter and honour ``Retry-After``.
  After :attr:`failure_budget` consecutive failures a service is *switched off* for the
  rest of the run and every later call raises :class:`ServiceUnavailable`. The caller
  records that as ``service_failed`` rather than routing around it. A vetting layer that
  gets this project blocked from MPC services is worse than no vetting layer.
* **a User-Agent that says who we are** and how to reach us, so an operator who wants the
  traffic to stop has an address to write to.

Only 2xx responses are cached. An error is a fact about a moment, not about the request,
and caching it would make a transient 504 permanent.
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import requests

#: Identifies the tool and a contact address. Deliberately says ``read-only``: this client
#: has no code path that issues anything but GET.
USER_AGENT = (
    "itf-linker/0.2 vetting (read-only; contact matthew.e.potts@gmail.com) "
    "python-requests"
)

#: Minimum seconds between two requests to the same host.
DEFAULT_MIN_INTERVAL_S = 1.0
#: Consecutive failures after which a service is abandoned for the rest of the run.
DEFAULT_FAILURE_BUDGET = 5
#: Status codes worth retrying. 403/404 are answers, not outages.
RETRY_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})


class ServiceUnavailable(RuntimeError):
    """Raised when a service has spent its failure budget and is no longer being called."""


@dataclass(slots=True)
class CachedResponse:
    status: int
    text: str
    url: str
    from_cache: bool
    elapsed_s: float

    def json(self) -> Any:
        return json.loads(self.text)


def _cache_key(service: str, url: str, params: dict[str, Any]) -> str:
    payload = json.dumps(
        {"service": service, "url": url, "params": {k: str(v) for k, v in sorted(params.items())}},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


class CachedSession:
    """Rate-limited, disk-cached, GET-only HTTP.

    ``stats`` accumulates the counts the M2 report quotes, so the "how many requests did
    this actually cost" question is answered by the client itself rather than estimated.
    """

    def __init__(
        self,
        cache_dir: Path,
        *,
        min_interval_s: float = DEFAULT_MIN_INTERVAL_S,
        max_retries: int = 3,
        backoff_base_s: float = 4.0,
        failure_budget: int = DEFAULT_FAILURE_BUDGET,
        user_agent: str = USER_AGENT,
        timeout: float = 120.0,
        offline: bool = False,
        sleeper: Any = time.sleep,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.min_interval_s = min_interval_s
        self.max_retries = max_retries
        self.backoff_base_s = backoff_base_s
        self.failure_budget = failure_budget
        self.timeout = timeout
        self.offline = offline
        self._sleep = sleeper
        self._session = requests.Session()
        self._session.headers["User-Agent"] = user_agent
        self._last_request: dict[str, float] = {}
        self._consecutive_failures: dict[str, int] = {}
        self.disabled: dict[str, str] = {}
        self.stats: dict[str, dict[str, int]] = {}

    # -- bookkeeping ---------------------------------------------------------------
    def _stat(self, service: str, key: str, n: int = 1) -> None:
        self.stats.setdefault(service, {}).setdefault(key, 0)
        self.stats[service][key] += n

    def _path(self, service: str, key: str) -> Path:
        return self.cache_dir / service / f"{key}.json"

    def cached_only(self, service: str, url: str, params: dict[str, Any]) -> CachedResponse | None:
        path = self._path(service, _cache_key(service, url, params))
        if not path.exists():
            return None
        try:
            blob = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return CachedResponse(
            status=blob["status"], text=blob["text"], url=blob.get("url", url),
            from_cache=True, elapsed_s=blob.get("elapsed_s", 0.0),
        )

    def _store(self, service: str, key: str, resp: requests.Response, elapsed: float) -> None:
        path = self._path(service, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "service": service,
                    "url": resp.url,
                    "status": resp.status_code,
                    "elapsed_s": round(elapsed, 3),
                    "fetched_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "text": resp.text,
                },
                indent=1,
            ),
            encoding="utf-8",
        )

    # -- politeness ----------------------------------------------------------------
    def _throttle(self, host: str) -> None:
        last = self._last_request.get(host)
        if last is not None:
            wait = self.min_interval_s - (time.monotonic() - last)
            if wait > 0:
                self._sleep(wait)
        self._last_request[host] = time.monotonic()

    def _record_failure(self, service: str, why: str) -> None:
        self._consecutive_failures[service] = self._consecutive_failures.get(service, 0) + 1
        self._stat(service, "failures")
        if self._consecutive_failures[service] >= self.failure_budget:
            self.disabled[service] = (
                f"{self._consecutive_failures[service]} consecutive failures; "
                f"last: {why}. Stopped querying this service."
            )

    # -- the only public verb ------------------------------------------------------
    def get(
        self,
        service: str,
        url: str,
        params: dict[str, Any],
        *,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> CachedResponse:
        """GET ``url``, from cache if possible, obeying the rate limit and failure budget.

        ``max_retries`` overrides the session default for one call. SBIDENT uses it: a
        four-minute request that times out has not hit a transient blip, it has hit a
        computation the service cannot finish, and repeating it three more times only
        spends someone else's CPU to learn the same thing.
        """
        retries = self.max_retries if max_retries is None else max_retries
        key = _cache_key(service, url, params)
        hit = self.cached_only(service, url, params)
        if hit is not None:
            self._stat(service, "cache_hits")
            return hit

        if service in self.disabled:
            raise ServiceUnavailable(f"{service}: {self.disabled[service]}")
        if self.offline:
            raise ServiceUnavailable(f"{service}: offline mode and no cached response")

        host = urlsplit(url).netloc
        last_error = "unknown"
        for attempt in range(retries + 1):
            self._throttle(host)
            started = time.monotonic()
            try:
                resp = self._session.get(
                    url, params=params, timeout=timeout or self.timeout, allow_redirects=True
                )
            except requests.RequestException as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                resp = None
            elapsed = time.monotonic() - started
            self._stat(service, "requests")

            if resp is not None and 200 <= resp.status_code < 300:
                self._consecutive_failures[service] = 0
                self._store(service, key, resp, elapsed)
                return CachedResponse(
                    status=resp.status_code, text=resp.text, url=resp.url,
                    from_cache=False, elapsed_s=elapsed,
                )

            if resp is not None:
                last_error = f"HTTP {resp.status_code}"
                if resp.status_code not in RETRY_STATUS:
                    self._record_failure(service, last_error)
                    raise ServiceUnavailable(f"{service}: {last_error} (not retryable)")

            if attempt < retries:
                delay = self.backoff_base_s * (2**attempt) * (1.0 + random.random() * 0.25)
                if resp is not None:
                    try:
                        delay = max(delay, float(resp.headers.get("Retry-After", 0)))
                    except (TypeError, ValueError):
                        pass
                self._stat(service, "retries")
                self._sleep(delay)

        self._record_failure(service, last_error)
        raise ServiceUnavailable(
            f"{service}: gave up after {retries + 1} attempt(s) ({last_error})"
        )

    def summary(self) -> dict[str, Any]:
        return {
            "user_agent": self._session.headers["User-Agent"],
            "min_interval_s": self.min_interval_s,
            "max_retries": self.max_retries,
            "failure_budget": self.failure_budget,
            "cache_dir": str(self.cache_dir),
            "per_service": self.stats,
            "disabled": self.disabled,
        }
