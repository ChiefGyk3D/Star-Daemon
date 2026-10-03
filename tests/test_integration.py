"""
End-to-end test: run the real daemon entry point as a subprocess against a
local fake GitHub API and a local fake Matrix homeserver, and watch a newly
starred repository get announced.

This is the "run it and look at it" check: it exercises the actual
``python star-daemon.py`` invocation (config loading, seeding, polling loop,
connector wiring), not just the units.
"""

import http.server
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from tests.fake_github import FakeGitHubAPI

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class FakeBackend(http.server.BaseHTTPRequestHandler):
    """Serves both the GitHub REST API and the Matrix client-server API."""

    api: FakeGitHubAPI = None
    matrix_posts = None

    def log_message(self, *args):
        pass

    def _send(self, status, payload, headers=None):
        body = json.dumps(payload).encode() if payload is not None else b""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/_matrix/"):
            self._send(200, {})  # room state probe from test_connection()
            return
        url = f"http://{self.headers.get('Host')}{self.path}"
        response = self.api.get(url, headers=dict(self.headers))
        self._send(response.status_code, response.json(), dict(response.headers))

    def do_POST(self):
        if "/send/m.room.message" in self.path:
            length = int(self.headers.get("Content-Length", 0))
            event = json.loads(self.rfile.read(length))
            self.matrix_posts.append(event)
            self._send(200, {"event_id": f"$event{len(self.matrix_posts)}"})
            return
        self._send(404, {"error": "unexpected POST"})


def test_daemon_announces_new_star_end_to_end(tmp_path):
    api = FakeGitHubAPI(repo_count=250)
    matrix_posts = []
    FakeBackend.api = api
    FakeBackend.matrix_posts = matrix_posts

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeBackend)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"

    state_file = tmp_path / "state.json"
    env = {
        **os.environ,
        # Explicitly pin every platform toggle: the developer's real .env is
        # loaded by the daemon and must not reach real services from a test.
        "GITHUB_ACCESS_TOKEN": "test-token-not-real",
        "GITHUB_USERNAME": "",
        "GITHUB_API_URL": base,
        "STATE_FILE": str(state_file),
        "CHECK_INTERVAL": "1",
        "RESYNC_INTERVAL": "0",
        "LOG_LEVEL": "INFO",
        "MASTODON_ENABLED": "false",
        "BLUESKY_ENABLED": "false",
        "DISCORD_ENABLED": "false",
        "MATRIX_ENABLED": "true",
        "MATRIX_HOMESERVER": base,
        "MATRIX_USER_ID": "@stardaemon:example.org",
        "MATRIX_PASSWORD": "",
        "MATRIX_ACCESS_TOKEN": "matrix-test-token",
        "MATRIX_ROOM_ID": "!testroom:example.org",
        "DOPPLER_TOKEN": "",
        "AWS_SECRET_NAME": "",
        "VAULT_ADDR": "",
    }

    process = subprocess.Popen(
        [sys.executable, "star-daemon.py"],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        # Wait for the seed to complete (state file written with all repos).
        deadline = time.time() + 30
        while time.time() < deadline:
            if state_file.exists():
                state = json.loads(state_file.read_text())
                if len(state.get("starred_repos", [])) == 250:
                    break
            time.sleep(0.2)
        else:
            pytest.fail("daemon never seeded its state file")

        assert matrix_posts == [], "seeding must not announce existing stars"
        requests_after_seed = api.request_count

        # Star something new and wait for the announcement.
        api.star("integration/new-star")
        deadline = time.time() + 30
        while time.time() < deadline and not matrix_posts:
            time.sleep(0.2)

        assert matrix_posts, "daemon never announced the newly starred repo"
        assert "integration/new-star" in matrix_posts[0]["body"]

        state = json.loads(state_file.read_text())
        assert "integration/new-star" in state["starred_repos"]
    finally:
        process.terminate()
        try:
            output, _ = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate()
        server.shutdown()

    assert "Monitoring GitHub stars for user: testuser" in output
    assert "Initial run: tracking 250 starred repositories" in output
    assert "New star detected: integration/new-star" in output
    assert "Successfully posted to Matrix" in output
