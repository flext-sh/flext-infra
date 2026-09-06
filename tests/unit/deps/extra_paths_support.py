"""Shared test helpers for extra-path manager contracts."""

from __future__ import annotations

from pathlib import Path

from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager

_TEST_REPOSITORY_ROOT = Path(__file__).resolve().parent


class ExtraPathsTestSupport:
    """Factory helpers for validated extra-path manager instances."""

    @staticmethod
    def manager(repository_root: Path | None = None) -> FlextInfraExtraPathsManager:
        """Return a manager built through the Pydantic validation path."""
        return FlextInfraExtraPathsManager(
            repository_root=repository_root or _TEST_REPOSITORY_ROOT
        )


__all__: list[str] = ["ExtraPathsTestSupport"]
