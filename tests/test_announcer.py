# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
The AI star announcer: prompts, guardrail handling, and the daemon's
fallback to MESSAGE_TEMPLATE when the LLM can't deliver.
"""

from unittest.mock import Mock

import pytest

import star_daemon
from star_announcer import CONTENT_MAX_CHARS, StarAnnouncer
from tests.fake_github import FakeGitHubAPI
from tests.test_daemon import DummyConnector, make_daemon, seed

REPO = {
    "full_name": "sharkdp/bat",
    "name": "bat",
    "description": "A cat(1) clone with wings",
    "language": "Rust",
    "topics": ["cli", "rust", "terminal"],
}
URL = "https://github.com/sharkdp/bat"
GOOD = "Just starred bat — a modern cat clone in Rust with syntax highlighting."


def make_announcer(response=GOOD, guardrail_result=None):
    announcer = StarAnnouncer.__new__(StarAnnouncer)
    announcer.enabled = True
    announcer.engine = Mock()
    announcer.engine.generate.return_value = response
    announcer.engine.apply_guardrails.return_value = (
        guardrail_result if guardrail_result is not None else (response, [])
    )
    return announcer


class TestCompose:
    def test_message_gets_url_appended(self):
        announcer = make_announcer()
        result = announcer.compose(REPO, URL)
        assert result == f"{GOOD}\n\n{URL}"

    def test_prompt_contains_only_known_facts(self):
        announcer = make_announcer()
        announcer.compose(REPO, URL)
        prompt = announcer.engine.generate.call_args[0][0]
        assert "sharkdp/bat" in prompt
        assert "A cat(1) clone with wings" in prompt
        assert "Rust" in prompt
        assert "cli" in prompt
        # The character budget is stated in the prompt.
        assert str(CONTENT_MAX_CHARS) in prompt

    def test_missing_description_still_composes(self):
        announcer = make_announcer()
        bare = {"full_name": "x/y", "name": "y"}
        assert announcer.compose(bare, "https://github.com/x/y") is not None

    def test_generation_failure_returns_none(self):
        announcer = make_announcer(response=None)
        assert announcer.compose(REPO, URL) is None

    def test_guardrail_failure_returns_none(self):
        """A hallucinated star count must never be posted."""
        announcer = make_announcer(
            response="Starred bat! 50k stars and trending!",
            guardrail_result=(
                None,
                ["Possible hallucination detected: '\\d+[km]?\\s+stars?'"],
            ),
        )
        assert announcer.compose(REPO, URL) is None

    def test_disabled_announcer_returns_none(self):
        announcer = make_announcer()
        announcer.enabled = False
        assert announcer.compose(REPO, URL) is None
        announcer.engine.generate.assert_not_called()

    def test_meta_text_and_urls_stripped(self):
        announcer = make_announcer(
            response=f'Here\'s your post: "{GOOD} https://spam.example"'
        )
        announcer.compose(REPO, URL)
        cleaned = announcer.engine.apply_guardrails.call_args[0][0]
        assert cleaned.startswith("Just starred")
        assert "spam.example" not in cleaned


class TestDaemonIntegration:
    def test_ai_message_used_when_available(self, tmp_path):
        api = FakeGitHubAPI(repo_count=5)
        daemon = make_daemon(tmp_path, api)
        seed(daemon, api)
        daemon.announcer = make_announcer()
        api.star("cool/project")

        daemon.check_new_stars()

        message, metadata = daemon.connectors[0].posts[0]
        assert message.startswith(GOOD)
        assert message.endswith("https://github.com/cool/project")

    def test_template_fallback_when_llm_fails(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            star_daemon.config,
            "message_template",
            "I just starred {name} on GitHub: {url}",
        )
        api = FakeGitHubAPI(repo_count=5)
        daemon = make_daemon(tmp_path, api)
        seed(daemon, api)
        daemon.announcer = make_announcer(response=None)
        api.star("cool/project")

        daemon.check_new_stars()

        message, _ = daemon.connectors[0].posts[0]
        assert (
            message
            == "I just starred cool/project on GitHub: https://github.com/cool/project"
        )

    def test_no_announcer_uses_template(self, tmp_path, monkeypatch):
        """Daemon constructed without an announcer (pre-LLM state) still posts."""
        monkeypatch.setattr(
            star_daemon.config,
            "message_template",
            "I just starred {name} on GitHub: {url}",
        )
        api = FakeGitHubAPI(repo_count=5)
        daemon = make_daemon(tmp_path, api)
        seed(daemon, api)
        assert daemon.announcer is None
        api.star("cool/project")

        daemon.check_new_stars()
        assert len(daemon.connectors[0].posts) == 1


class TestRealGuardrails:
    """compose() against the real hypeman guardrails (no mocked apply_guardrails)."""

    def _announcer_with_real_guardrails(self, generated):
        from hypeman_social.llm import STAR_PROFILE, LLMManager

        announcer = StarAnnouncer.__new__(StarAnnouncer)
        announcer.enabled = True
        engine = LLMManager(profile=STAR_PROFILE)
        engine.enabled = True
        # Only generation is faked; guardrails run for real against a
        # provider carrying the STAR_PROFILE.
        engine.generate = lambda prompt, max_tokens=None: generated

        from hypeman_social.llm.ollama import OllamaLLM

        provider = OllamaLLM(profile=STAR_PROFILE)
        engine.primary = provider
        announcer.engine = engine
        return announcer

    def test_hallucinated_star_count_is_rejected(self):
        announcer = self._announcer_with_real_guardrails(
            "Just starred bat — trending on GitHub with 50k stars!"
        )
        assert announcer.compose(REPO, URL) is None

    def test_honest_description_passes(self):
        announcer = self._announcer_with_real_guardrails(GOOD)
        result = announcer.compose(REPO, URL)
        assert result is not None
        assert result.endswith(URL)

    def test_invented_version_is_rejected(self):
        announcer = self._announcer_with_real_guardrails(
            "Just starred bat v2.3.1, a cat clone in Rust."
        )
        assert announcer.compose(REPO, URL) is None
