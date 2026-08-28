"""Tests for the daemon logic in star_daemon.py."""

import json

import pytest

import star_daemon
from connectors.base import Connector
from github_stars import StarWatcher
from star_daemon import StarDaemon
from tests.fake_github import FakeGitHubAPI


class DummyConnector(Connector):
    def __init__(self, fail=False):
        super().__init__("Dummy", enabled=True)
        self.fail = fail
        self.posts = []
        self._initialized = True

    def initialize(self):
        return True

    def test_connection(self):
        return True

    def post_message(self, message, metadata=None):
        if self.fail:
            raise RuntimeError("boom")
        self.posts.append((message, metadata))
        return True


def make_daemon(tmp_path, api, connectors=None):
    daemon = StarDaemon(state_file=tmp_path / "state.json")
    daemon.watcher = StarWatcher("test-token", session=api)
    daemon.connectors = connectors if connectors is not None else [DummyConnector()]
    return daemon


def seed(daemon, api):
    daemon.starred_repos = api.all_names()


class TestCheckNewStars:
    def test_new_star_is_posted_with_message_and_metadata(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            star_daemon.config,
            "message_template",
            "I just starred {name} on GitHub: {url}",
        )
        api = FakeGitHubAPI(repo_count=20)
        daemon = make_daemon(tmp_path, api)
        seed(daemon, api)
        api.star("cool/project")

        daemon.check_new_stars()

        connector = daemon.connectors[0]
        assert len(connector.posts) == 1
        message, metadata = connector.posts[0]
        assert message == (
            "I just starred cool/project on GitHub: " "https://github.com/cool/project"
        )
        assert metadata["repo_data"]["full_name"] == "cool/project"
        assert metadata["url"] == "https://github.com/cool/project"
        assert "cool/project" in daemon.starred_repos

    def test_no_new_stars_posts_nothing(self, tmp_path):
        api = FakeGitHubAPI(repo_count=20)
        daemon = make_daemon(tmp_path, api)
        seed(daemon, api)

        daemon.check_new_stars()

        assert daemon.connectors[0].posts == []

    def test_failing_connector_does_not_block_others_or_state(self, tmp_path):
        api = FakeGitHubAPI(repo_count=5)
        good = DummyConnector()
        daemon = make_daemon(
            tmp_path, api, connectors=[DummyConnector(fail=True), good]
        )
        seed(daemon, api)
        api.star("cool/project")

        daemon.check_new_stars()

        assert len(good.posts) == 1
        assert "cool/project" in daemon.starred_repos
        assert daemon.state_file.exists()

    def test_rate_limited_check_is_skipped_without_crash(self, tmp_path):
        api = FakeGitHubAPI(repo_count=5)
        daemon = make_daemon(tmp_path, api)
        seed(daemon, api)
        before = set(daemon.starred_repos)
        api.exhaust()

        daemon.check_new_stars()  # must not raise

        assert daemon.starred_repos == before
        assert daemon.connectors[0].posts == []


class TestState:
    def test_state_round_trips_across_daemon_instances(self, tmp_path):
        api = FakeGitHubAPI(repo_count=3)
        daemon = make_daemon(tmp_path, api)
        seed(daemon, api)
        api.star("cool/project")
        daemon.check_new_stars()

        reloaded = make_daemon(tmp_path, api)
        reloaded._load_state()

        assert reloaded.starred_repos == daemon.starred_repos

    def test_corrupt_state_file_is_treated_as_first_run(self, tmp_path):
        state_file = tmp_path / "state.json"
        state_file.write_text("{ not json !!!")
        daemon = StarDaemon(state_file=state_file)

        daemon._load_state()

        assert daemon.starred_repos == set()

    def test_state_file_is_valid_json_after_save(self, tmp_path):
        api = FakeGitHubAPI(repo_count=2)
        daemon = make_daemon(tmp_path, api)
        seed(daemon, api)
        daemon._save_state()

        state = json.loads(daemon.state_file.read_text())
        assert set(state["starred_repos"]) == api.all_names()
        assert "last_updated" in state


class TestResync:
    def test_resync_prunes_unstarred_repos(self, tmp_path, monkeypatch):
        monkeypatch.setattr(star_daemon.config, "resync_interval", 1)
        api = FakeGitHubAPI(repo_count=10)
        daemon = make_daemon(tmp_path, api)
        seed(daemon, api)
        daemon.starred_repos.add("gone/unstarred")  # no longer starred upstream
        daemon._last_resync = 0  # due immediately

        daemon.maybe_resync()

        assert "gone/unstarred" not in daemon.starred_repos
        assert daemon.starred_repos == api.all_names()

    def test_resync_disabled_makes_no_requests(self, tmp_path, monkeypatch):
        monkeypatch.setattr(star_daemon.config, "resync_interval", 0)
        api = FakeGitHubAPI(repo_count=10)
        daemon = make_daemon(tmp_path, api)
        daemon._last_resync = 0

        daemon.maybe_resync()

        assert api.request_count == 0


class TestBackoff:
    def test_low_quota_backs_off_until_reset(self, tmp_path, monkeypatch):
        monkeypatch.setattr(star_daemon.config, "check_interval", 300)
        api = FakeGitHubAPI(repo_count=5, remaining=10)
        daemon = make_daemon(tmp_path, api)
        seed(daemon, api)

        daemon.check_new_stars()
        delay = daemon._next_delay()

        assert delay > 300, (
            "with quota below the floor the daemon must wait until the "
            "rate-limit window resets instead of polling on the normal interval"
        )

    def test_healthy_quota_uses_check_interval(self, tmp_path, monkeypatch):
        monkeypatch.setattr(star_daemon.config, "check_interval", 300)
        api = FakeGitHubAPI(repo_count=5, remaining=4900)
        daemon = make_daemon(tmp_path, api)
        seed(daemon, api)

        daemon.check_new_stars()

        assert daemon._next_delay() == 300
