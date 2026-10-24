# Star-Daemon threat model

`star-daemon.threat-dragon.json` is an OWASP Threat Dragon v2 model (STRIDE) of
Star-Daemon: it polls the operator's GitHub starred list, optionally has an LLM
write the announcement, and posts to Mastodon, Bluesky, Discord, Matrix and
Threads. It is drawn from `star_daemon.py`, `github_stars.py`,
`star_announcer.py`, `platforms.py`, `config.py`, `docker/`, `scripts/` and
`.github/`, plus the pinned `hypeman-social` 0.3.4 source (read at its v0.3.4
tag), which does the posting and the LLM calls. It is not a full audit.

Open it: OWASP Threat Dragon (desktop or web app), File > Open, pick the JSON.
Each element's description cites the file and function it came from.

## Trust boundaries

- GitHub: the API is the transport; repository descriptions, topics and names are written by third parties.
- Daemon host or container: the process, its environment and its state file.
- LLM endpoint: Ollama (normally LAN) or Gemini (opt-in); receives untrusted text, returns text that gets posted.
- Social platforms: posts leave the trust domain and become public.
- Secrets provider: Doppler, AWS Secrets Manager, Vault or `.env`.
- Build and release supply chain: GitHub Actions callers of git-your-ship-together, Dependabot, GHCR and Docker Hub.

## Unverified items

- Threads connector (`hypeman_social/social/threads.py`) was not read.
- Transport security of the Doppler, AWS and Vault SDKs; Vault address is used as given.
- Whether the operator's Ollama server sits behind TLS or authentication.
- Gemini transport details beyond key handling.
- `.env.example` was not read.

## Open High and Critical threats

None open. Starring a private repository used to publish its name and
description (High); `star_daemon.py::_is_non_public` now skips private and
internal repositories, with tests in `tests/test_daemon.py::TestPrivateRepositories`.

## Open Medium threats worth a decision

- Prompt injection through repository description, name or topics.
- Untrusted model output posted publicly with thin output checks.
- Matrix messages built with unescaped repository text (in the dependency).
