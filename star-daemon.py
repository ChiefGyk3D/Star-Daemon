#!/usr/bin/env python3
"""
Star-Daemon entry point.

The daemon logic lives in ``star_daemon.py`` (an importable module name so the
test suite can exercise it); this shim keeps the documented
``python star-daemon.py`` invocation working for Docker, systemd, and the docs.
"""

from star_daemon import main

if __name__ == "__main__":
    main()
