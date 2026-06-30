"""Shared test helpers for extra-path manager contracts."""

from __future__ import annotations

from pathlib import Path

from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager

_TEST_WORKSPACE_ROOT = Path(__file__).resolve().parent


class ExtraPathsTestSupport:
    """Factory helpers for validated extra-path manager instances."""

    @staticmethod
    def manager(
        workspace_root: Path | None = None,
    ) -> FlextInfraExtraPathsManager:
        """Return a manager built through the Pydantic validation path."""
        return FlextInfraExtraPathsManager(
            workspace=workspace_root or _TEST_WORKSPACE_ROOT,
        )


__all__: list[str] = ["ExtraPathsTestSupport"]
