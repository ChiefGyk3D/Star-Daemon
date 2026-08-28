"""Tests for configuration parsing and validation."""

import os

import pytest

from config import Config

# Every variable the tests reason about gets pinned or removed, because the
# developer's real .env (loaded once at first import) leaks into os.environ.
CONTROLLED_VARS = [
    "CHECK_INTERVAL",
    "LOG_LEVEL",
    "STATE_FILE",
    "RESYNC_INTERVAL",
    "RATE_LIMIT_FLOOR",
    "GITHUB_USERNAME",
    "MESSAGE_TEMPLATE",
    "MASTODON_ENABLED",
    "MASTODON_API_BASE_URL",
    "MASTODON_CLIENT_ID",
    "MASTODON_CLIENT_SECRET",
    "MASTODON_ACCESS_TOKEN",
    "BLUESKY_ENABLED",
    "BLUESKY_HANDLE",
    "BLUESKY_APP_PASSWORD",
    "DISCORD_ENABLED",
    "DISCORD_WEBHOOK_URL",
    "DISCORD_ROLE_ID",
    "MATRIX_ENABLED",
    "MATRIX_HOMESERVER",
    "MATRIX_USER_ID",
    "MATRIX_PASSWORD",
    "MATRIX_ACCESS_TOKEN",
    "MATRIX_ROOM_ID",
    "DOPPLER_TOKEN",
    "AWS_SECRET_NAME",
    "VAULT_ADDR",
    "VAULT_TOKEN",
]


def make_config(monkeypatch, tmp_path, **env):
    # load_dotenv() resolves .env relative to config.py, so chdir alone is not
    # enough to keep the developer's real .env out of a fresh Config().
    monkeypatch.setattr("config.load_dotenv", lambda *a, **k: None)
    monkeypatch.chdir(tmp_path)
    for var in CONTROLLED_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("GITHUB_ACCESS_TOKEN", "test-token-not-real")
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return Config()


class TestDefaults:
    def test_check_interval_defaults_to_300_seconds(self, monkeypatch, tmp_path):
        config = make_config(monkeypatch, tmp_path)
        assert config.check_interval == 300

    def test_resync_and_rate_limit_defaults(self, monkeypatch, tmp_path):
        config = make_config(monkeypatch, tmp_path)
        assert config.resync_interval == 86400
        assert config.rate_limit_floor == 100

    def test_overrides_are_respected(self, monkeypatch, tmp_path):
        config = make_config(
            monkeypatch,
            tmp_path,
            CHECK_INTERVAL="60",
            RESYNC_INTERVAL="0",
            RATE_LIMIT_FLOOR="500",
        )
        assert config.check_interval == 60
        assert config.resync_interval == 0
        assert config.rate_limit_floor == 500

    def test_missing_github_token_raises(self, monkeypatch, tmp_path):
        monkeypatch.setattr("config.load_dotenv", lambda *a, **k: None)
        monkeypatch.chdir(tmp_path)
        for var in CONTROLLED_VARS:
            monkeypatch.delenv(var, raising=False)
        monkeypatch.delenv("GITHUB_ACCESS_TOKEN", raising=False)
        with pytest.raises(ValueError, match="GITHUB_ACCESS_TOKEN"):
            Config()


class TestValidation:
    def test_no_platform_enabled_fails_validation(self, monkeypatch, tmp_path):
        config = make_config(monkeypatch, tmp_path)
        assert config.validate() is False

    def test_discord_requires_webhook_url(self, monkeypatch, tmp_path):
        config = make_config(monkeypatch, tmp_path, DISCORD_ENABLED="true")
        assert config.validate() is False

    def test_discord_with_webhook_url_passes(self, monkeypatch, tmp_path):
        config = make_config(
            monkeypatch,
            tmp_path,
            DISCORD_ENABLED="true",
            DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/1/token",
        )
        assert config.validate() is True

    def test_mastodon_requires_url_and_token(self, monkeypatch, tmp_path):
        config = make_config(monkeypatch, tmp_path, MASTODON_ENABLED="true")
        assert config.validate() is False

    def test_matrix_requires_credentials(self, monkeypatch, tmp_path):
        config = make_config(
            monkeypatch,
            tmp_path,
            MATRIX_ENABLED="true",
            MATRIX_HOMESERVER="https://matrix.example.org",
            MATRIX_USER_ID="@bot:example.org",
            MATRIX_ROOM_ID="!room:example.org",
        )
        # homeserver/user/room present but neither password nor token
        assert config.validate() is False

    def test_bool_parsing(self, monkeypatch, tmp_path):
        for truthy in ("true", "1", "yes", "on", "TRUE"):
            config = make_config(
                monkeypatch,
                tmp_path,
                DISCORD_ENABLED=truthy,
                DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/1/t",
            )
            assert config.discord_enabled is True, truthy
        config = make_config(monkeypatch, tmp_path, DISCORD_ENABLED="false")
        assert config.discord_enabled is False
