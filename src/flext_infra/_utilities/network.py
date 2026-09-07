"""Read-only network reachability preflight."""

from __future__ import annotations

from http.client import HTTPConnection, HTTPException, HTTPSConnection
from urllib.parse import urlsplit


class FlextInfraUtilitiesNetwork:
    """Decide once, before effects, whether an endpoint answers at all."""

    @staticmethod
    def endpoint_reachable(url: str, *, timeout_seconds: float) -> bool:
        """Return whether one HEAD request receives any HTTP answer in time.

        A server that answers with an error status (403 from a rate limit, 404)
        is reachable: the network path exists and a later authenticated call
        can succeed. Only a connection failure or a timeout means offline. The
        endpoint must be ``http`` or ``https``; any other scheme is a caller
        defect and raises.
        """
        parts = urlsplit(url)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            msg = f"reachability probe requires an http(s) URL, got {url!r}"
            raise ValueError(msg)
        connection_type = HTTPSConnection if parts.scheme == "https" else HTTPConnection
        connection = connection_type(
            parts.hostname, parts.port, timeout=timeout_seconds
        )
        try:
            connection.request("HEAD", parts.path or "/")
            connection.getresponse()
        except (HTTPException, OSError):
            return False
        else:
            return True
        finally:
            connection.close()


__all__: list[str] = ["FlextInfraUtilitiesNetwork"]
