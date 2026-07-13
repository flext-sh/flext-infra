"""Project candidate discovery for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c
from flext_infra._utilities._project_discovery_shape import (
    FlextInfraUtilitiesProjectDiscoveryShapeMixin,
)
from flext_infra._utilities.git_scope import FlextInfraUtilitiesGitScope
from flext_infra._utilities.pyproject import FlextInfraUtilitiesPyproject

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class FlextInfraUtilitiesProjectDiscoveryCandidatesMixin(
    FlextInfraUtilitiesProjectDiscoveryShapeMixin,
):
    """Private candidate enumeration for workspace project discovery."""

    @classmethod
    def discover_external_workspace_roots(
        cls,
        workspace_root: Path,
        *,
        scan_dirs: frozenset[str] | None = None,
    ) -> t.SequenceOf[Path]:
        """Return FLEXT-managed sibling workspace roots selected by policy."""
        resolved_workspace_root = workspace_root.resolve()
        parent = resolved_workspace_root.parent
        if not parent.is_dir():
            return ()
        effective_scan_dirs = scan_dirs or frozenset()
        configured_member_set = frozenset(
            FlextInfraUtilitiesPyproject.workspace_member_names(workspace_root),
        )
        roots: list[Path] = []
        seen: set[Path] = set()
        for pattern in c.Infra.EXTERNAL_WORKSPACE_SIBLING_PATTERNS:
            for candidate in sorted(parent.glob(pattern), key=lambda item: item.name):
                resolved_candidate = candidate.resolve()
                if resolved_candidate == resolved_workspace_root:
                    continue
                if resolved_candidate in seen:
                    continue
                if not cls._looks_like_project(
                    resolved_candidate,
                    effective_scan_dirs=effective_scan_dirs,
                    configured_member_set=configured_member_set,
                ):
                    continue
                roots.append(resolved_candidate)
                seen.add(resolved_candidate)
        return tuple(roots)

    @classmethod
    def discover_project_candidates(
        cls,
        workspace_root: Path,
        *,
        scan_dirs: frozenset[str] | None = None,
        include_attached: bool = False,
    ) -> t.SequenceOf[Path]:
        """Return all canonical project candidates before consumer-specific filtering."""
        roots: t.MutableSequenceOf[Path] = []
        effective_scan_dirs = scan_dirs or frozenset()
        configured_members = FlextInfraUtilitiesPyproject.workspace_member_names(
            workspace_root,
        )
        configured_member_set = frozenset(configured_members)
        resolved_workspace_root = workspace_root.resolve()
        tracked_child_dirs = (
            FlextInfraUtilitiesGitScope.git_tracked_top_level_dir_names(
                resolved_workspace_root,
            )
        )
        attached_child_dirs = (
            cls._attached_top_level_dir_names(resolved_workspace_root)
            if include_attached
            else frozenset()
        )
        external_workspace_roots = (
            cls.discover_external_workspace_roots(
                resolved_workspace_root,
                scan_dirs=scan_dirs,
            )
            if include_attached
            else ()
        )

        if cls._looks_like_project(
            resolved_workspace_root,
            effective_scan_dirs=effective_scan_dirs,
            configured_member_set=configured_member_set,
        ) and FlextInfraUtilitiesGitScope.project_descriptor_is_tracked(
            resolved_workspace_root,
            resolved_workspace_root,
        ):
            roots.append(resolved_workspace_root)
        if tracked_child_dirs is None and not attached_child_dirs:
            candidate_entries: t.SequenceOf[Path] = sorted(
                workspace_root.iterdir(),
                key=lambda item: item.name,
            )
        else:
            candidate_entries = [
                resolved_workspace_root / dir_name
                for dir_name in sorted(
                    frozenset(tracked_child_dirs or ()) | attached_child_dirs,
                )
            ]
        roots.extend(
            [
                entry.resolve()
                for entry in candidate_entries
                if entry.is_dir()
                and not entry.name.startswith(".")
                and (
                    entry.name in attached_child_dirs
                    or FlextInfraUtilitiesGitScope.project_descriptor_is_tracked(
                        resolved_workspace_root,
                        entry.resolve(),
                    )
                )
                and cls._looks_like_project(
                    entry.resolve(),
                    effective_scan_dirs=effective_scan_dirs,
                    configured_member_set=configured_member_set,
                )
            ],
        )
        roots.extend(external_workspace_roots)
        if not roots and (resolved_workspace_root / c.Infra.DEFAULT_SRC_DIR).is_dir():
            return [resolved_workspace_root]
        return roots


__all__: list[str] = ["FlextInfraUtilitiesProjectDiscoveryCandidatesMixin"]
