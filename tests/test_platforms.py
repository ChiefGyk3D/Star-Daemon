"""
The hypeman-social wiring: env-name bridge, connector adapter, and
registry-driven construction.
"""

import os
from types import SimpleNamespace

import pytest
from hypeman_social.social import EVENT_STAR

import platforms
from platforms import PlatformConnector, bridge_config_to_env, build_connectors


@pytest.fixture(autouse=True)
def clean_environ():
    """The bridge writes into os.environ; undo it after every test here."""
    saved = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(saved)


def make_config(**overrides):
    """A Config-shaped namespace with everything off unless overridden."""
    base = dict(
        mastodon_enabled=False,
        mastodon_api_base_url="",
        mastodon_client_id="",
        mastodon_client_secret="",
        mastodon_access_token="",
        bluesky_enabled=False,
        bluesky_handle="",
        bluesky_app_password="",
        discord_enabled=False,
        discord_webhook_url="",
        discord_role_id="",
        matrix_enabled=False,
        matrix_homeserver="",
        matrix_room_id="",
        matrix_user_id="",
        matrix_password="",
        matrix_access_token="",
        threads_enabled=False,
        threads_access_token="",
        threads_user_id="",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class TestEnvBridge:
    def test_renamed_variables_are_translated(self, monkeypatch):
        for var in (
            "MATRIX_ENABLE_POSTING",
            "MATRIX_USERNAME",
            "DISCORD_ROLE",
            "DISCORD_ENABLE_POSTING",
        ):
            monkeypatch.delenv(var, raising=False)

        cfg = make_config(
            matrix_enabled=True,
            matrix_homeserver="https://m.example",
            matrix_room_id="!r:m.example",
            matrix_user_id="@bot:m.example",
            discord_enabled=True,
            discord_webhook_url="https://d.example/wh",
            discord_role_id="42",
        )
        bridge_config_to_env(cfg)

        import os

        assert os.environ["MATRIX_ENABLE_POSTING"] == "true"
        assert os.environ["MATRIX_USERNAME"] == "@bot:m.example"
        assert os.environ["DISCORD_ENABLE_POSTING"] == "true"
        assert os.environ["DISCORD_ROLE"] == "42"

    def test_disabled_platforms_export_nothing(self, monkeypatch):
        monkeypatch.delenv("BLUESKY_ENABLE_POSTING", raising=False)
        bridge_config_to_env(make_config())
        import os

        assert "BLUESKY_ENABLE_POSTING" not in os.environ

    def test_explicit_hypeman_name_wins(self, monkeypatch):
        # An operator who already adopted the hypeman convention is not
        # overridden by the legacy translation.
        monkeypatch.setenv("MASTODON_ENABLE_POSTING", "false")
        bridge_config_to_env(make_config(mastodon_enabled=True))
        import os

        assert os.environ["MASTODON_ENABLE_POSTING"] == "false"


class FakePlatform:
    """Stands in for a hypeman SocialPlatform."""

    def __init__(self, name="Fake", post_id="post-1"):
        self.name = name
        self.post_id = post_id
        self.posted = []

    def authenticate(self):
        return True

    def test_connection(self):
        return True

    def safe_post(self, message, **kwargs):
        self.posted.append({"message": message, **kwargs})
        return self.post_id


class TestPlatformConnector:
    def test_metadata_maps_to_star_stream_data(self):
        platform = FakePlatform()
        connector = PlatformConnector(platform)
        assert connector.initialize() is True

        metadata = {
            "url": "https://github.com/o/r",
            "repo_data": {"full_name": "o/r"},
            "thumbnail_url": "https://a.example/x.png",
        }
        ok = connector.safe_post("starred!", metadata)

        assert ok is True
        sent = platform.posted[0]
        assert sent["message"] == "starred!"
        assert sent["stream_data"]["event_kind"] == EVENT_STAR
        assert sent["stream_data"]["repo_data"] == {"full_name": "o/r"}
        assert sent["stream_data"]["thumbnail_url"] == "https://a.example/x.png"
        assert metadata["last_post_id"] == "post-1"

    def test_failed_post_returns_false(self):
        platform = FakePlatform(post_id=None)
        connector = PlatformConnector(platform)
        connector.initialize()
        assert connector.safe_post("starred!", {}) is False

    def test_none_metadata_is_fine(self):
        platform = FakePlatform()
        connector = PlatformConnector(platform)
        connector.initialize()
        assert connector.safe_post("starred!", None) is True


class TestBuildConnectors:
    def test_only_enabled_platforms_survive(self, monkeypatch):
        # Nothing enabled -> nothing built (each platform's authenticate()
        # returns False without its enable flag).
        for var in list(__import__("os").environ):
            if var.endswith("_ENABLE_POSTING"):
                monkeypatch.delenv(var, raising=False)
        connectors = build_connectors(make_config())
        assert connectors == []

    def test_discord_defaults_to_star_events(self, monkeypatch):
        monkeypatch.delenv("DISCORD_ENABLE_POSTING", raising=False)
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://d.example/wh")
        cfg = make_config(
            discord_enabled=True, discord_webhook_url="https://d.example/wh"
        )
        connectors = build_connectors(cfg)
        assert len(connectors) == 1
        assert connectors[0].name == "Discord"
        assert connectors[0].platform.default_event_kind == EVENT_STAR

    def test_probe_failure_drops_the_platform(self, monkeypatch):
        monkeypatch.delenv("DISCORD_ENABLE_POSTING", raising=False)
        cfg = make_config(
            discord_enabled=True, discord_webhook_url="https://d.example/wh"
        )
        monkeypatch.setattr(
            platforms.PlatformConnector, "test_connection", lambda self: False
        )
        assert build_connectors(cfg) == []
