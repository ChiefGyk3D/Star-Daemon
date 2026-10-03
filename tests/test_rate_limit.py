"""
Regression tests for the GitHub rate-limit bug.

The daemon used to materialise the ENTIRE paginated starred list on every
check (ceil(N/30) API requests per check, 60 times an hour), which grows
without bound as stars accumulate and eventually exhausts the 5,000/hour
budget on its own. These tests pin the fixed behaviour: a check costs one
API request no matter how many repositories are starred, ordering is
requested explicitly, and unchanged checks are free (ETag/304).
"""

import time

import pytest

from github_stars import MAX_PAGES_PER_CHECK, RateLimitError, StarWatcher
from tests.fake_github import FakeGitHubAPI


def make_watcher(api, **kwargs):
    return StarWatcher("test-token", session=api, **kwargs)


class TestPerCheckCostIsConstant:
    @pytest.mark.parametrize("total_starred", [10, 150, 1500, 5000])
    def test_idle_check_costs_one_request_regardless_of_star_count(self, total_starred):
        """THE regression test: per-check cost must not scale with N."""
        api = FakeGitHubAPI(repo_count=total_starred)
        watcher = make_watcher(api)
        known = api.all_names()

        api.request_count = 0
        new = watcher.fetch_new_starred(known)

        assert new == []
        assert api.request_count == 1, (
            f"a no-change check against {total_starred} starred repos made "
            f"{api.request_count} API requests; it must make exactly 1. "
            "Fix: fetch only page 1 of /user/starred (sort=created, "
            "direction=desc) and stop at the first already-known repository "
            "instead of walking the entire paginated starred list."
        )

    def test_one_new_star_costs_one_request(self):
        api = FakeGitHubAPI(repo_count=2000)
        watcher = make_watcher(api)
        known = api.all_names()
        new_repo = api.star("someone/shiny-new-repo")

        api.request_count = 0
        new = watcher.fetch_new_starred(known)

        assert [r["full_name"] for r in new] == ["someone/shiny-new-repo"]
        assert new[0]["html_url"] == new_repo["html_url"]
        assert api.request_count == 1, (
            "detecting one new star must still cost exactly 1 request; "
            "stop paginating at the first known repository"
        )


class TestExplicitOrdering:
    def test_newest_first_ordering_is_requested_explicitly(self):
        """The 'new star is on page 1' assumption must be guaranteed by the
        request, not by the API's default ordering."""
        api = FakeGitHubAPI(repo_count=50)
        watcher = make_watcher(api)

        watcher.fetch_new_starred(api.all_names())

        _, params, _ = api.requests[-1]
        assert params.get("sort") == "created", (
            "the starred request must pass sort=created explicitly; "
            "relying on the API default ordering is not allowed"
        )
        assert params.get("direction") == "desc", (
            "the starred request must pass direction=desc explicitly so the "
            "newest star is guaranteed to be on page 1"
        )

    def test_per_page_100_is_requested(self):
        api = FakeGitHubAPI(repo_count=50)
        watcher = make_watcher(api)

        watcher.fetch_new_starred(api.all_names())

        _, params, _ = api.requests[-1]
        assert (
            params.get("per_page") == "100"
        ), "requests must use per_page=100, not PyGithub's default of 30"


class TestConditionalRequests:
    def test_unchanged_check_sends_etag_and_consumes_no_quota(self):
        api = FakeGitHubAPI(repo_count=300)
        watcher = make_watcher(api)
        known = api.all_names()

        watcher.fetch_new_starred(known)  # primes the ETag
        quota_before = api.remaining

        new = watcher.fetch_new_starred(known)

        assert new == []
        _, _, headers = api.requests[-1]
        assert headers.get(
            "If-None-Match"
        ), "repeat checks must send If-None-Match with the stored ETag"
        assert api.last_status == 304
        assert api.remaining == quota_before, (
            "GitHub does not count 304 responses against the rate limit; an "
            "unchanged check must consume zero quota"
        )

    def test_change_after_304_is_still_detected(self):
        api = FakeGitHubAPI(repo_count=300)
        watcher = make_watcher(api)
        known = api.all_names()

        watcher.fetch_new_starred(known)  # 200, primes ETag
        watcher.fetch_new_starred(known)  # 304
        api.star("someone/fresh-repo")

        new = watcher.fetch_new_starred(known)
        assert [r["full_name"] for r in new] == ["someone/fresh-repo"]


class TestNewStarDetection:
    def test_multiple_new_stars_returned_oldest_first(self):
        api = FakeGitHubAPI(repo_count=500)
        watcher = make_watcher(api)
        known = api.all_names()
        api.star("first/starred")
        api.star("second/starred")  # newest

        new = watcher.fetch_new_starred(known)

        assert [r["full_name"] for r in new] == ["first/starred", "second/starred"], (
            "new stars must be returned oldest-first so announcements post "
            "in chronological order"
        )

    def test_overflow_beyond_one_page_paginates_until_overlap(self):
        api = FakeGitHubAPI(repo_count=500)
        watcher = make_watcher(api)
        known = api.all_names()
        for i in range(150):
            api.star(f"burst/repo-{i}")

        api.request_count = 0
        new = watcher.fetch_new_starred(known)

        assert len(new) == 150
        assert api.request_count == 2, (
            "150 new stars at per_page=100 should cost exactly 2 requests "
            "(page 2 hits a known repository and stops)"
        )

    def test_runaway_pagination_is_capped(self):
        api = FakeGitHubAPI(repo_count=100 * (MAX_PAGES_PER_CHECK + 3))
        watcher = make_watcher(api)

        api.request_count = 0
        watcher.fetch_new_starred(known=set())  # nothing known: worst case

        assert api.request_count == MAX_PAGES_PER_CHECK, (
            "an incremental check must never walk more than "
            f"{MAX_PAGES_PER_CHECK} pages"
        )


class TestRateLimitHandling:
    def test_exhausted_quota_raises_rate_limit_error(self):
        api = FakeGitHubAPI(repo_count=10)
        api.exhaust()
        watcher = make_watcher(api)

        with pytest.raises(RateLimitError) as excinfo:
            watcher.fetch_new_starred(api.all_names())
        assert excinfo.value.reset_epoch == api.reset_epoch

    def test_remaining_quota_is_tracked_and_low_quota_triggers_backoff(self):
        api = FakeGitHubAPI(repo_count=10, remaining=42)
        watcher = make_watcher(api, rate_limit_floor=100)

        watcher.fetch_new_starred(api.all_names())

        assert watcher.rate_limit_remaining == 41
        assert watcher.quota_low() is True
        assert 0 < watcher.seconds_until_reset() <= 3600

    def test_healthy_quota_does_not_back_off(self):
        api = FakeGitHubAPI(repo_count=10, remaining=4000)
        watcher = make_watcher(api, rate_limit_floor=100)

        watcher.fetch_new_starred(api.all_names())

        assert watcher.quota_low() is False


class TestFullEnumeration:
    def test_fetch_all_walks_every_page_once(self):
        api = FakeGitHubAPI(repo_count=250)
        watcher = make_watcher(api)

        api.request_count = 0
        names = watcher.fetch_all_starred()

        assert names == api.all_names()
        assert api.request_count == 3  # ceil(250 / 100)
