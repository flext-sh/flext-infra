"""Shared typed behavior for CLI route services."""

from __future__ import annotations

from flext_infra import t


class CliRouteBase:
    """Provide the common result-value widening contract for route handlers."""

    @staticmethod
    def as_route_value(value: t.Cli.ResultValue) -> t.Cli.ResultValue:
        """Widen a concrete result payload to the CLI route contract value."""
        return value


__all__: list[str] = ["CliRouteBase"]
