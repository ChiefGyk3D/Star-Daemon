"""Required-secret handling: placeholders and empty values fail closed.

One rule (config.is_placeholder) covers every secret and credential-like value.
Error messages name the variable and never print the value.
"""

import logging

import pytest

from config import is_placeholder
from tests.test_config import make_config

# Built from short parts so the source holds no token-shaped literal for the
# secret scanner; the joined value is still not a placeholder.
REAL_TOKEN = "-".join(["tok", "9f3a", "7c1d", "52e8"])

PLACEHOLDERS = [
    "",
    "   ",
    "your_github_token_here",
    "YOUR_GITHUB_TOKEN_HERE",
    "Your_Matrix_Password",
    "changeme",
    "ChangeMe123",
    "<token>",
    "<your token>",
    "example",
    "PLACEHOLDER",
    "xxx",
    "xxxxxxxx",
    "dp.st.your_service_token",
    "https://discord.com/api/webhooks/your_webhook_url",
    "https://your.mastodon.instance",
    "@your_user:matrix.org",
    "!your_room_id:matrix.org",
    "your.handle.bsky.social",
]

REAL_VALUES = [
    REAL_TOKEN,
    "https://discord.com/api/webhooks/1234567890/abcDEF-ghi_JKL",
    "https://mastodon.social",
    "@bot:matrix.org",
    "alice.bsky.social",
    "abcd-efgh-ijkl-mnop",
]


class TestPlaceholderRule:
    @pytest.mark.parametrize("value", PLACEHOLDERS)
    def test_placeholder_detected(self, value):
        assert is_placeholder(value) is True

    @pytest.mark.parametrize("value", REAL_VALUES)
    def test_real_value_accepted(self, value):
        assert is_placeholder(value) is False

    def test_none_is_placeholder(self):
        assert is_placeholder(None) is True


class TestGithubToken:
    @pytest.mark.parametrize(
        "value", ["your_github_token_here", "YOUR_TOKEN", "changeme", "", "  "]
    )
    def test_rejected_and_value_not_leaked(self, monkeypatch, tmp_path, value):
        with pytest.raises(ValueError) as exc:
            make_config(monkeypatch, tmp_path, GITHUB_ACCESS_TOKEN=value)
        assert "GITHUB_ACCESS_TOKEN" in str(exc.value)
        if value.strip():
            assert value not in str(exc.value)

    def test_unset_rejected(self, monkeypatch, tmp_path):
        import config as config_module

        monkeypatch.setattr("config.load_dotenv", lambda *a, **k: None)
        monkeypatch.delenv("GITHUB_ACCESS_TOKEN", raising=False)
        with pytest.raises(ValueError, match="GITHUB_ACCESS_TOKEN"):
            config_module.Config()

    def test_real_value_accepted(self, monkeypatch, tmp_path):
        cfg = make_config(monkeypatch, tmp_path, GITHUB_ACCESS_TOKEN=REAL_TOKEN)
        assert cfg.github_token == REAL_TOKEN


# (enabled flag, {variable: real value}) for each platform's required values.
PLATFORMS = {
    "MASTODON_ENABLED": {
        "MASTODON_API_BASE_URL": "https://mastodon.social",
        "MASTODON_ACCESS_TOKEN": REAL_TOKEN,
    },
    "BLUESKY_ENABLED": {
        "BLUESKY_HANDLE": "alice.bsky.social",
        "BLUESKY_APP_PASSWORD": "abcd-efgh-ijkl-mnop",
    },
    "DISCORD_ENABLED": {
        "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/1234567890/abcDEF",
    },
    "MATRIX_ENABLED": {
        "MATRIX_HOMESERVER": "https://matrix.org",
        "MATRIX_USER_ID": "@bot:matrix.org",
        "MATRIX_ROOM_ID": "!room1234:matrix.org",
        "MATRIX_PASSWORD": REAL_TOKEN,
    },
    "THREADS_ENABLED": {
        "THREADS_ACCESS_TOKEN": REAL_TOKEN,
        "THREADS_USER_ID": "1234567890",
    },
}

PLACEHOLDER_FOR = "your_value_here"


def platform_env(enabled_var):
    env = {enabled_var: "true"}
    env.update(PLATFORMS[enabled_var])
    return env


class TestValidate:
    @pytest.mark.parametrize("enabled_var", sorted(PLATFORMS))
    def test_real_values_accepted(self, monkeypatch, tmp_path, enabled_var):
        for var in ("THREADS_ENABLED", "THREADS_ACCESS_TOKEN", "THREADS_USER_ID"):
            monkeypatch.delenv(var, raising=False)
        cfg = make_config(monkeypatch, tmp_path, **platform_env(enabled_var))
        assert cfg.validate() is True

    @pytest.mark.parametrize(
        "enabled_var,variable",
        [(e, v) for e, vs in sorted(PLATFORMS.items()) for v in vs],
    )
    @pytest.mark.parametrize("bad", [PLACEHOLDER_FOR, "YOUR_VALUE", "changeme", ""])
    def test_placeholder_or_empty_rejected(
        self, monkeypatch, tmp_path, caplog, enabled_var, variable, bad
    ):
        for var in ("THREADS_ENABLED", "THREADS_ACCESS_TOKEN", "THREADS_USER_ID"):
            monkeypatch.delenv(var, raising=False)
        env = platform_env(enabled_var)
        env[variable] = bad
        cfg = make_config(monkeypatch, tmp_path, **env)
        with caplog.at_level(logging.ERROR):
            assert cfg.validate() is False
        assert variable in caplog.text
        if bad:
            assert bad not in caplog.text

    def test_matrix_password_placeholder_without_token_rejected(
        self, monkeypatch, tmp_path, caplog
    ):
        env = platform_env("MATRIX_ENABLED")
        env["MATRIX_PASSWORD"] = "your_matrix_password"
        cfg = make_config(monkeypatch, tmp_path, **env)
        with caplog.at_level(logging.ERROR):
            assert cfg.validate() is False
        assert "MATRIX_PASSWORD" in caplog.text
        assert "your_matrix_password" not in caplog.text

    def test_matrix_placeholder_password_ignored_when_real_token_present(
        self, monkeypatch, tmp_path
    ):
        env = platform_env("MATRIX_ENABLED")
        env["MATRIX_PASSWORD"] = "your_matrix_password"
        env["MATRIX_ACCESS_TOKEN"] = REAL_TOKEN
        cfg = make_config(monkeypatch, tmp_path, **env)
        assert cfg.validate() is True

    def test_disabled_platform_with_placeholders_is_logged_not_fatal(
        self, monkeypatch, tmp_path, caplog
    ):
        env = platform_env("DISCORD_ENABLED")
        env["MATRIX_ENABLED"] = "false"
        env["MATRIX_PASSWORD"] = "your_matrix_password"
        cfg = make_config(monkeypatch, tmp_path, **env)
        with caplog.at_level(logging.INFO):
            assert cfg.validate() is True
        assert "Matrix" in caplog.text and "disabled" in caplog.text
        assert "your_matrix_password" not in caplog.text
