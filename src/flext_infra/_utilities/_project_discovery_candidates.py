"""Repository-local project candidate discovery."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra._utilities._project_discovery_shape import (
    FlextInfraUtilitiesProjectDiscoveryShapeMixin,
)

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class FlextInfraUtilitiesProjectDiscoveryCandidatesMixin(
    FlextInfraUtilitiesProjectDiscoveryShapeMixin
):
    """Discover only the repository explicitly supplied by the consumer."""

    @classmethod
    def discover_project_candidates(
        cls, workspace_root: Path, *, scan_dirs: frozenset[str] | None = None
    ) -> t.SequenceOf[Path]:
        """Return the current repository when it has a valid project shape."""
        resolved_root = workspace_root.resolve()
        effective_scan_dirs = scan_dirs or frozenset()
        return (
            [resolved_root]
            if cls._looks_like_project(
                resolved_root, effective_scan_dirs=effective_scan_dirs
            )
            else []
        )


__all__: list[str] = ["FlextInfraUtilitiesProjectDiscoveryCandidatesMixin"]
