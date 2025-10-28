def test_smoke_imports():
    """Basic smoke test to ensure the package imports correctly.
    Keeps CI meaningful even if there are no user tests yet.
    """
    import config
    from connectors import (
        MastodonConnector,
        BlueSkyConnector,
        DiscordConnector,
        MatrixConnector,
    )

    assert config is not None
    assert MastodonConnector is not None
    assert BlueSkyConnector is not None
    assert DiscordConnector is not None
    assert MatrixConnector is not None
