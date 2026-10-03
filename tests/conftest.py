"""Shared test setup.

Must run before any project module is imported: ``config.py`` instantiates a
global Config at import time, which requires GITHUB_ACCESS_TOKEN and would try
to reach a secrets manager if one appears configured in the environment.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Never let the test process talk to a real secrets manager.
for _var in ("DOPPLER_TOKEN", "AWS_SECRET_NAME", "VAULT_ADDR", "VAULT_TOKEN"):
    os.environ.pop(_var, None)

os.environ.setdefault("GITHUB_ACCESS_TOKEN", "test-token-not-real")
