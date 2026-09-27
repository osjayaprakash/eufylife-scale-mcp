"""Errors raised by EufyLifeClient. Messages never contain names or measurements."""

from __future__ import annotations


class EufyLifeError(Exception):
    """Base class for every client error."""


class AuthenticationError(EufyLifeError):
    """Session expired, token rejected, or no login yet."""


class LoginRejectedError(EufyLifeError):
    """The login call answered with a non-success `res_code` (usually bad credentials)."""

    def __init__(self, code: int, message: str = "") -> None:
        self.code = code
        self.message = message
        detail = f": {message}" if message else ""
        super().__init__(f"EufyLife rejected the login (code {code}{detail})")


class RateLimitError(EufyLifeError):
    def __init__(self, retry_after: int | None) -> None:
        self.retry_after = retry_after
        super().__init__(f"Rate limited (retry after {retry_after})")


class APIError(EufyLifeError):
    """Unexpected HTTP status, or a non-success `res_code` in the response body."""

    def __init__(self, status: int) -> None:
        self.status = status
        super().__init__(f"EufyLife API error {status}")


class NetworkError(EufyLifeError):
    """Connection failure or timeout; `kind` is the transport error class name."""

    def __init__(self, kind: str) -> None:
        self.kind = kind
        super().__init__(f"Network error: {kind}")


class ResponseShapeError(EufyLifeError):
    """A response did not have the expected shape; `call` names the client method."""

    def __init__(self, call: str) -> None:
        self.call = call
        super().__init__(f"Unexpected response shape from {call}")
