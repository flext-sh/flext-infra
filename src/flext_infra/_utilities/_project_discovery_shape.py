"""Project shape helpers for flext-infra discovery utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c
from flext_infra._utilities import (
    FlextInfraUtilitiesDependencies,
    FlextInfraUtilitiesPyproject,
)

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraUtilitiesProjectDiscoveryShapeMixin:
    """Private project-shape predicates for workspace project discovery."""

    @classmethod
    def _is_nonparticipant(
        cls,
        candidate: Path,
        repository_root: Path,
        nonparticipants: frozenset[str],
    ) -> bool:
        """Return whether one candidate lies under a declared non-participant.

        Returns:
            Whether the candidate is excluded by the current declaration.

        """
        resolved = candidate.resolve()
        root = repository_root.resolve()
        if not resolved.is_relative_to(root):
            return False
        posix = resolved.relative_to(root).as_posix()
        if posix in {".", ""}:
            return False
        return any(
            posix == declared or posix.startswith(f"{declared}/")
            for declared in nonparticipants
        )

    @staticmethod
    def _looks_like_project(
        path: Path,
        *,
        effective_scan_dirs: frozenset[str],
        configured_project_set: frozenset[str],
    ) -> bool:
        """Return whether one path matches the canonical governed project shape.

        Returns:
            Whether one path matches the canonical governed project shape.

        """
        if not path.is_dir():
            return False
        pyproject_path = path / c.PYPROJECT_FILENAME
        if pyproject_path.exists() and (
            path.name in configured_project_set
            or (path / c.Infra.MAKEFILE_FILENAME).exists()
        ):
            return True
        payload = FlextInfraUtilitiesPyproject.pyproject_payload(pyproject_path)
        if not payload:
            return False
        dependency_names: set[str] = set(
            FlextInfraUtilitiesDependencies.declared_dependency_names_from_payload(
                payload,
            ),
        )
        if c.Infra.PKG_CORE in dependency_names:
            return True
        if effective_scan_dirs:
            return any((path / dir_name).is_dir() for dir_name in effective_scan_dirs)
        return True


__all__: list[str] = ["FlextInfraUtilitiesProjectDiscoveryShapeMixin"]
