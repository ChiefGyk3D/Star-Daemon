"""
An in-memory fake of GitHub's starred-repositories REST API.

Faithful to the pieces the daemon relies on: per_page pagination with RFC 5988
``Link`` headers, newest-first ordering, ETag/If-None-Match conditional
requests (304s do not consume quota, mirroring GitHub), and
``X-RateLimit-Remaining``/``X-RateLimit-Reset`` headers.
"""

import hashlib
import json
import time
from urllib.parse import parse_qsl, urlparse

import requests
from requests.structures import CaseInsensitiveDict


def make_repo(index: int) -> dict:
    """Repo dict shaped like the REST API's starred-list items."""
    return {
        "full_name": f"owner{index}/repo-{index}",
        "name": f"repo-{index}",
        "html_url": f"https://github.com/owner{index}/repo-{index}",
        "description": f"Test repository {index}",
        "language": "Python",
        "stargazers_count": index,
        "forks_count": index // 2,
        "owner": {"avatar_url": f"https://avatars.example/{index}.png"},
    }


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else []
        self.headers = CaseInsensitiveDict(headers or {})

    @property
    def links(self):
        header = self.headers.get("Link")
        if not header:
            return {}
        return {link["rel"]: link for link in requests.utils.parse_header_links(header)}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeGitHubAPI:
    """Stands in for a requests.Session pointed at api.github.com."""

    def __init__(self, repo_count=0, remaining=5000, limit=5000):
        # Newest first, matching sort=created&direction=desc. Higher index =
        # starred more recently.
        self.repos = [make_repo(i) for i in range(repo_count, 0, -1)]
        self.remaining = remaining
        self.limit = limit
        self.reset_epoch = int(time.time()) + 3600
        self.request_count = 0
        self.requests = []  # (url, params, headers) per request
        self.last_status = None

    # -- test helpers -----------------------------------------------------

    def star(self, full_name: str) -> dict:
        """Star a new repo (prepends: it is now the newest)."""
        repo = make_repo(0)
        repo["full_name"] = full_name
        repo["name"] = full_name.split("/")[-1]
        repo["html_url"] = f"https://github.com/{full_name}"
        self.repos.insert(0, repo)
        return repo

    def all_names(self):
        return {repo["full_name"] for repo in self.repos}

    def exhaust(self):
        self.remaining = 0

    # -- fake transport ---------------------------------------------------

    def _etag(self):
        digest = hashlib.sha256(
            json.dumps([r["full_name"] for r in self.repos]).encode()
        ).hexdigest()
        return f'"{digest}"'

    def _rate_headers(self):
        return {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(self.reset_epoch),
        }

    def get(self, url, params=None, headers=None, timeout=None):
        self.request_count += 1
        headers = dict(headers or {})

        # Follow-up page requests carry their query string in the URL.
        parsed = urlparse(url)
        merged = dict(parse_qsl(parsed.query))
        merged.update({k: str(v) for k, v in (params or {}).items()})
        self.requests.append((url, merged, headers))

        if self.remaining <= 0:
            self.last_status = 403
            return FakeResponse(
                403, {"message": "API rate limit exceeded"}, self._rate_headers()
            )

        if parsed.path.endswith("/user"):
            self.remaining -= 1
            self.last_status = 200
            return FakeResponse(200, {"login": "testuser"}, {**self._rate_headers()})

        page = int(merged.get("page", "1"))
        per_page = int(merged.get("per_page", "30"))
        direction = merged.get("direction", "desc")  # GitHub's default

        # Conditional request: nothing changed -> 304, quota untouched.
        if page == 1 and headers.get("If-None-Match") == self._etag():
            self.last_status = 304
            return FakeResponse(304, None, self._rate_headers())

        self.remaining -= 1
        ordered = self.repos if direction == "desc" else list(reversed(self.repos))
        start = (page - 1) * per_page
        items = ordered[start : start + per_page]

        response_headers = {**self._rate_headers(), "ETag": self._etag()}
        if start + per_page < len(ordered):
            next_query = "&".join(
                f"{k}={v}" for k, v in {**merged, "page": page + 1}.items()
            )
            next_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{next_query}"
            response_headers["Link"] = f'<{next_url}>; rel="next"'

        self.last_status = 200
        return FakeResponse(200, items, response_headers)
