"""Project discovery helpers for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra.typings import t
from flext_infra._utilities._project_discovery_candidates import (
    FlextInfraUtilitiesProjectDiscoveryCandidatesMixin,
)
from flext_infra._utilities.pyproject import FlextInfraUtilitiesPyproject


class FlextInfraUtilitiesProjectDiscovery(
    FlextInfraUtilitiesProjectDiscoveryCandidatesMixin
):
    """Static helpers for discovering governed project roots in a workspace."""

    @classmethod
    def discover_project_roots(
        cls,
        workspace_root: Path,
        *,
        scan_dirs: frozenset[str] | None = None,
        include_attached: bool = False,
    ) -> t.SequenceOf[Path]:
        """Discover all project directories under workspace root.

        Algorithm:
          1. Check if workspace_root itself looks like a project
          2. Enumerate ``.gitmodules``-tracked submodules of the workspace
          3. When explicitly requested, surface external members declared by
             path or glob in the workspace's pyproject.
          4. Return sorted list including the workspace root itself

        Args:
            workspace_root: Root directory to start search from.
            scan_dirs: Directory names indicating a project exists (e.g., "src", "tests").
                Must be frozenset for use as constant. Defaults to standard project dirs.
            include_attached: Include explicitly declared external workspace members.

        Returns:
            List of project root paths sorted by ``.gitmodules`` order, with
            the workspace root prepended when it satisfies project shape, and
            attached external repos appended in alphabetical order.

        """
        configured_members = FlextInfraUtilitiesPyproject.workspace_member_names(
            workspace_root
        )
        candidates = cls.discover_project_candidates(
            workspace_root, scan_dirs=scan_dirs, include_attached=include_attached
        )
        resolved_workspace_root = workspace_root.resolve()
        if not configured_members:
            return candidates
        configured_order = {name: idx for idx, name in enumerate(configured_members)}
        ordered: list[Path] = []
        non_root_candidates = sorted(
            (c for c in candidates if c != resolved_workspace_root),
            key=lambda candidate: (
                configured_order.get(candidate.name, len(configured_members)),
                candidate.name,
            ),
        )
        ordered.extend(non_root_candidates)
        return ordered


__all__: list[str] = ["FlextInfraUtilitiesProjectDiscovery"]
