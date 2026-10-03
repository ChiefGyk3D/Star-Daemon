"""
GitHub starred-repository polling with a fixed per-check API cost.

The daemon previously listed *every* starred repository on every check via
PyGithub (``ceil(N / 30)`` requests per check, forever growing with N). This
module replaces that with:

- A single request for the first page of ``/user/starred``, explicitly ordered
  newest-first (``sort=created&direction=desc``), stopping at the first
  already-known repository. Steady-state cost: 1 request per check, regardless
  of how many repositories are starred.
- Conditional requests via ``ETag``/``If-None-Match``. GitHub does not count
  304 responses against the rate limit, so an idle check costs no quota at all.
- Rate-limit introspection: ``X-RateLimit-Remaining``/``X-RateLimit-Reset`` are
  parsed on every response and logged, and callers can back off when the
  remaining quota drops below a floor instead of silently draining it.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Set

import requests

logger = logging.getLogger(__name__)

API_BASE = "https://api.github.com"

# Safety cap for one incremental check. With per_page=100 this is only ever
# exceeded if >1000 repos were starred between two checks, which indicates
# something is wrong (e.g. corrupted state); the periodic resync will heal it.
MAX_PAGES_PER_CHECK = 10

REQUEST_TIMEOUT = 30


class RateLimitError(Exception):
    """Raised when GitHub rejects a request because the rate limit is exhausted."""

    def __init__(self, message: str, reset_epoch: Optional[int] = None):
        super().__init__(message)
        self.reset_epoch = reset_epoch


class StarWatcher:
    """Polls GitHub for newly starred repositories at O(1) API cost per check."""

    def __init__(
        self,
        token: str,
        username: Optional[str] = None,
        api_base: str = API_BASE,
        per_page: int = 100,
        rate_limit_floor: int = 100,
        session: Optional[requests.Session] = None,
    ):
        self._token = token
        self._username = username
        self._api_base = api_base.rstrip("/")
        self._per_page = per_page
        self._rate_limit_floor = rate_limit_floor
        self._session = session or requests.Session()
        self._etag: Optional[str] = None

        # Updated from response headers on every request
        self.rate_limit_remaining: Optional[int] = None
        self.rate_limit_reset: Optional[int] = None

    @property
    def starred_url(self) -> str:
        if self._username:
            return f"{self._api_base}/users/{self._username}/starred"
        return f"{self._api_base}/user/starred"

    def _request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "star-daemon",
        }
        if extra_headers:
            headers.update(extra_headers)

        response = self._session.get(
            url, params=params, headers=headers, timeout=REQUEST_TIMEOUT
        )
        self._record_rate_limit(response)

        if response.status_code in (403, 429) and self._is_rate_limited(response):
            reset = self.rate_limit_reset
            raise RateLimitError(
                "GitHub API rate limit exhausted"
                + (f" (resets at epoch {reset})" if reset else ""),
                reset_epoch=reset,
            )
        response.raise_for_status()
        return response

    def _record_rate_limit(self, response: requests.Response) -> None:
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset = response.headers.get("X-RateLimit-Reset")
        if remaining is not None:
            try:
                self.rate_limit_remaining = int(remaining)
                if reset is not None:
                    self.rate_limit_reset = int(reset)
            except ValueError:
                return
            logger.debug(
                "GitHub rate limit: %s remaining (resets at epoch %s)",
                self.rate_limit_remaining,
                self.rate_limit_reset,
            )
            if self.rate_limit_remaining < self._rate_limit_floor:
                logger.warning(
                    "GitHub rate limit low: %s remaining (floor: %s, resets at epoch %s)",
                    self.rate_limit_remaining,
                    self._rate_limit_floor,
                    self.rate_limit_reset,
                )

    def _is_rate_limited(self, response: requests.Response) -> bool:
        if response.headers.get("Retry-After"):
            return True
        return response.headers.get("X-RateLimit-Remaining") == "0"

    def quota_low(self) -> bool:
        """True when the remaining quota is below the configured floor."""
        return (
            self.rate_limit_remaining is not None
            and self.rate_limit_remaining < self._rate_limit_floor
        )

    def seconds_until_reset(self) -> int:
        """Seconds until the rate-limit window resets (0 if unknown/past)."""
        if self.rate_limit_reset is None:
            return 0
        return max(0, int(self.rate_limit_reset - time.time()))

    def viewer_login(self) -> str:
        """Return the login of the authenticated user (1 API request)."""
        response = self._request(f"{self._api_base}/user")
        return response.json()["login"]

    def fetch_new_starred(self, known: Set[str]) -> List[Dict[str, Any]]:
        """
        Return repositories starred since ``known`` was recorded, oldest first.

        Requests page 1 of the starred list explicitly ordered newest-first and
        stops at the first repository already present in ``known``, so the cost
        is one API request per check regardless of the total number of starred
        repositories. Uses a conditional request (ETag): when nothing changed,
        GitHub answers 304, which does not count against the rate limit.
        """
        params = {
            # Explicit ordering: the newest star must be on page 1. Do not
            # rely on the API's default ordering.
            "sort": "created",
            "direction": "desc",
            "per_page": self._per_page,
        }
        conditional = {"If-None-Match": self._etag} if self._etag else None
        response = self._request(
            self.starred_url, params=params, extra_headers=conditional
        )

        if response.status_code == 304:
            return []

        # Only the first-page request participates in ETag caching.
        self._etag = response.headers.get("ETag")

        new_repos: List[Dict[str, Any]] = []
        pages = 1
        while True:
            for item in response.json():
                full_name = item.get("full_name")
                if full_name is None:
                    continue
                if full_name in known:
                    # Everything after this is older and therefore known.
                    return list(reversed(new_repos))
                new_repos.append(item)

            next_url = response.links.get("next", {}).get("url")
            if not next_url:
                return list(reversed(new_repos))
            if pages >= MAX_PAGES_PER_CHECK:
                logger.warning(
                    "Stopped incremental star check after %s pages without "
                    "finding a known repository; the periodic resync will "
                    "pick up anything missed",
                    pages,
                )
                return list(reversed(new_repos))
            response = self._request(next_url)
            pages += 1

    def fetch_all_starred(self) -> Set[str]:
        """
        Return the full set of starred repository names.

        Walks every page (``ceil(N / per_page)`` requests), so this is only for
        the initial seed and the periodic resync — never the per-check path.
        """
        names: Set[str] = set()
        params = {
            "sort": "created",
            "direction": "desc",
            "per_page": self._per_page,
        }
        response = self._request(self.starred_url, params=params)
        while True:
            for item in response.json():
                full_name = item.get("full_name")
                if full_name:
                    names.add(full_name)
            next_url = response.links.get("next", {}).get("url")
            if not next_url:
                return names
            response = self._request(next_url)
