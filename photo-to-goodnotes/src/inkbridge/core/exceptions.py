"""Exception types for future integration boundaries."""


class InkBridgeError(Exception):
    """Base application error."""


class UnsupportedFormatError(InkBridgeError):
    """Input format has no available adapter."""


class RendererUnavailableError(InkBridgeError):
    """An actual Goodnotes rendering has not been supplied."""
