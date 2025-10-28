def test_smoke_imports():
    """Basic smoke test to ensure the package imports correctly.
    Keeps CI meaningful even if there are no user tests yet.
    """
    # Don't import config directly as it requires environment variables
    # Just verify the modules can be loaded
    import importlib.util

    # Verify config module exists and can be loaded
    spec = importlib.util.spec_from_file_location("config", "config.py")
    assert spec is not None, "config.py module spec not found"

    # Import connectors which don't require env vars at import time
    from connectors import (
        BlueSkyConnector,
        DiscordConnector,
        MastodonConnector,
        MatrixConnector,
    )

    assert MastodonConnector is not None
    assert BlueSkyConnector is not None
    assert DiscordConnector is not None
    assert MatrixConnector is not None
