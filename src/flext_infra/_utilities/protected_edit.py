"""Protected file edit helpers facade."""

from __future__ import annotations

from flext_infra import (
    FlextInfraUtilitiesProtectedEditWrites,
)


class FlextInfraUtilitiesProtectedEdit(FlextInfraUtilitiesProtectedEditWrites):
    """Shared safety helpers for protected file edits in refactor workflows."""

    pass


__all__: list[str] = ["FlextInfraUtilitiesProtectedEdit"]
