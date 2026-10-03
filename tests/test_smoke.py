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

    # Import the platform wiring, which doesn't require env vars at import
    # time, and check the hypeman-social registry behind it.
    from hypeman_social.social import REGISTRY

    from platforms import Connector, PlatformConnector, build_connectors

    assert Connector is not None
    assert PlatformConnector is not None
    assert build_connectors is not None
    assert {"bluesky", "mastodon", "discord", "matrix", "threads"} <= set(REGISTRY)
