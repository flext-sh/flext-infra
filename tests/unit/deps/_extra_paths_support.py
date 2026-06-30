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
        validated = FlextInfraExtraPathsManager.model_validate(
            {"workspace": str(workspace_root or _TEST_WORKSPACE_ROOT)},
        )
        if isinstance(validated, FlextInfraExtraPathsManager):
            return validated
        msg = "FlextInfraExtraPathsManager validation returned unexpected model"
        raise TypeError(msg)


__all__: list[str] = ["ExtraPathsTestSupport"]
