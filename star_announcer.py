# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
AI-written star announcements, powered by hypeman-social.

Instead of the bare template ("I just starred X: <url>"), the daemon can ask
an LLM to say what the project actually *is* — a sentence or two drawn from
the repository's name, description, language, and topics. Runs against a
local Ollama server (gemma3 by default) exactly like the other daemons, with
Gemini available as provider or failover.

Configuration (same keys as Boon-Tube-Daemon and stream-daemon):

    LLM_ENABLE=true
    LLM_PROVIDER=ollama            # or gemini
    LLM_OLLAMA_HOST=http://your-ollama-box
    LLM_OLLAMA_PORT=11434
    LLM_OLLAMA_MODEL=gemma3:4b
    LLM_FALLBACK_PROVIDER=gemini   # optional, opt-in failover

The guardrails matter more here than anywhere else: a model asked to describe
a repo it cannot see will happily invent star counts, versions, and "trending
on GitHub". hypeman's STAR_PROFILE rejects a message containing any of those,
and the daemon then falls back to the honest template.
"""

import logging
import re
from typing import Any, Dict, Optional

from hypeman_social.llm import STAR_PROFILE, LLMManager

logger = logging.getLogger(__name__)

#: Keep generated content well under Bluesky's 300-grapheme limit so the
#: same message (plus URL) fits every connected platform.
CONTENT_MAX_CHARS = 220


class StarAnnouncer:
    """
    Generates a short explanation of a starred repository.

    Wraps hypeman-social's LLMManager (reconnection, retries, failover).
    When disabled or unavailable, compose() returns None and the daemon
    uses its configured MESSAGE_TEMPLATE instead — a star is never left
    unannounced because the AI box is down.
    """

    def __init__(self):
        self.engine = LLMManager(profile=STAR_PROFILE)
        self.enabled = False

    def initialize(self) -> bool:
        """Bring up the configured provider(s). False when LLM_ENABLE is off."""
        if self.engine.authenticate():
            self.enabled = True
            logger.info(f"Star announcer ready (provider: {self.engine.provider})")
        return self.enabled

    def status(self) -> Dict[str, Any]:
        """Provider state, for logging and diagnostics."""
        return self.engine.status()

    def compose(self, repo_data: Dict[str, Any], url: str) -> Optional[str]:
        """
        Write an announcement that explains what the starred project is.

        Args:
            repo_data: Repository fields (full_name, description, language,
                topics) as provided by the GitHub API.
            url: The repository URL, appended after validation.

        Returns:
            The finished message with URL, or None when generation failed or
            the message didn't survive the anti-hallucination guardrails —
            the caller falls back to its template either way.
        """
        if not self.enabled:
            return None

        name = repo_data.get("full_name") or repo_data.get("name") or ""
        description = (repo_data.get("description") or "").strip()
        language = repo_data.get("language") or ""
        topics = repo_data.get("topics") or []

        prompt = self._build_prompt(name, description, language, topics)

        message = self.engine.generate(prompt)
        if not message:
            logger.warning("Star announcer: generation failed, using template")
            return None

        message = self._strip_meta_text(message)

        cleaned, issues = self.engine.apply_guardrails(
            message,
            title=description or name,
            username=name.split("/")[0] if "/" in name else name,
            platform="generic",
            char_limit=CONTENT_MAX_CHARS,
            expected_hashtag_count=0,
        )
        if not cleaned:
            logger.warning(
                f"Star announcer: message failed guardrails ({'; '.join(issues)}), "
                f"using template"
            )
            return None

        logger.info(f"✨ Generated star announcement: {cleaned[:60]}...")
        return f"{cleaned}\n\n{url}"

    @staticmethod
    def _build_prompt(name: str, description: str, language: str, topics) -> str:
        """
        Prompt tuned for small local models (gemma3:4b class).

        The hard rule is honesty: the model only knows what we hand it, so
        every instruction pushes it toward rephrasing the facts it has and
        away from inventing the ones it doesn't.
        """
        facts = [f'REPOSITORY: "{name}"']
        if description:
            facts.append(f'DESCRIPTION: "{description}"')
        if language:
            facts.append(f"PRIMARY LANGUAGE: {language}")
        if topics:
            facts.append(f'TOPICS: {", ".join(str(t) for t in topics[:8])}')
        facts_block = "\n".join(facts)

        return f"""You are a developer sharing a GitHub project you just starred, explaining briefly what it is and why it's interesting.

KNOWN FACTS (this is ALL you know about the project):
{facts_block}

TASK: Write a short post (1-2 sentences) that says you starred this project and explains what it does, in your own words.

RULES (FOLLOW EXACTLY):
✓ Length: MUST be {CONTENT_MAX_CHARS} characters or less
✓ Output: ONLY the post text (no quotes, no meta-commentary, no "Here's...")
✓ Rephrase the description naturally — explain it like you'd tell a colleague
✓ Mention you starred it (e.g. "Just starred...", "Starred X today —", "Added a star to...")
✗ DO NOT include any URL (it's added automatically)
✗ DO NOT include hashtags
✗ DO NOT invent anything not in the facts above: no star counts, no version
  numbers, no "trending", no release dates, no contributor counts, no
  features the description doesn't mention
✗ DO NOT use hype words: "INSANE", "EPIC", "game-changer", "revolutionary", "must-see"

EXAMPLES OF GOOD POSTS:

Facts: "sharkdp/bat" — "A cat(1) clone with wings" — Rust
Good: "Just starred bat — a modern take on cat written in Rust, with syntax highlighting and git integration baked in. My terminal thanks me."

Facts: "excalidraw/excalidraw" — "Virtual whiteboard for sketching hand-drawn like diagrams" — TypeScript
Good: "Starred Excalidraw today. A virtual whiteboard for sketching diagrams that look hand-drawn — great for architecture doodles that shouldn't look too official."

BAD examples to AVOID:
✗ "Just starred this AMAZING project with 50k stars!" (invented star count, hype)
✗ "Check out v2.3.1 of this trending repo!" (invented version, invented trending)

NOW: Write the post for "{name}". Under {CONTENT_MAX_CHARS} characters. No hashtags, no URLs.

Post:"""

    @staticmethod
    def _strip_meta_text(message: str) -> str:
        """Remove model chatter and any URL it invented."""
        message = message.strip()
        message = re.sub(
            r"^(?:Here\'?s|Okay,? here\'?s|Sure|Certainly)[^:\n]*:\s*",
            "",
            message,
            flags=re.IGNORECASE,
        )
        message = message.strip().strip('"').strip()
        message = re.sub(r"https?://[^\s]+", "", message)
        message = re.sub(r"[ \t]{2,}", " ", message)
        return message.strip()
