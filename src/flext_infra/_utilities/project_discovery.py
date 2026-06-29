"""Project discovery helpers for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_cli import u
from flext_infra import c, t
from flext_infra._utilities.dependencies import FlextInfraUtilitiesDependencies
from flext_infra._utilities.git_scope import FlextInfraUtilitiesGitScope
from flext_infra._utilities.pyproject import FlextInfraUtilitiesPyproject


class FlextInfraUtilitiesProjectDiscovery:
    """Static helpers for discovering governed project roots in a workspace."""

    @staticmethod
    def discover_project_roots(
        workspace_root: Path,
        *,
        scan_dirs: frozenset[str] | None = None,
    ) -> t.SequenceOf[Path]:
        """Discover all project directories under workspace root.

        Algorithm:
          1. Check if workspace_root itself looks like a project
          2. Enumerate ``.gitmodules``-tracked submodules of the workspace
          3. Surface external sub-repos that opt-in via
             ``[tool.flext.workspace] attached = true`` in their pyproject
             (covers any external git repo that imports flext-core but lives
             outside the workspace's submodule registry — name-agnostic,
             discovered purely by directory layout and pyproject content)
          4. Return sorted list including the workspace root itself

        Args:
            workspace_root: Root directory to start search from.
            scan_dirs: Directory names indicating a project exists (e.g., "src", "tests").
                Must be frozenset for use as constant. Defaults to standard project dirs.

        Returns:
            List of project root paths sorted by ``.gitmodules`` order, with
            the workspace root prepended when it satisfies project shape, and
            attached external repos appended in alphabetical order.

        """
        configured_members = FlextInfraUtilitiesPyproject.workspace_member_names(
            workspace_root,
        )
        candidates = FlextInfraUtilitiesProjectDiscovery.discover_project_candidates(
            workspace_root,
            scan_dirs=scan_dirs,
            include_attached=True,
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

    @staticmethod
    def _looks_like_project(
        path: Path,
        *,
        effective_scan_dirs: frozenset[str],
        configured_member_set: frozenset[str],
    ) -> bool:
        """Return whether one path matches the canonical governed project shape."""
        result = False
        if path.is_dir():
            pyproject_path = path / c.Infra.PYPROJECT_FILENAME
            if pyproject_path.exists() and (
                path.name in configured_member_set
                or (path / c.Infra.MAKEFILE_FILENAME).exists()
            ):
                result = True
            else:
                payload = FlextInfraUtilitiesPyproject.pyproject_payload(pyproject_path)
                if payload:
                    dependency_names: set[str] = set(
                        FlextInfraUtilitiesDependencies.declared_dependency_names_from_payload(
                            payload,
                        )
                    )
                    if c.Infra.PKG_CORE in dependency_names:
                        result = True
                    elif effective_scan_dirs:
                        result = any(
                            (path / dir_name).is_dir()
                            for dir_name in effective_scan_dirs
                        )
                    else:
                        result = True
        return result

    @classmethod
    def _attached_top_level_dir_names(cls, scope_root: Path) -> frozenset[str]:
        """Return top-level dir names opted into workspace iteration as attached.

        A directory is "attached" only when its ``pyproject.toml`` declares
        ``[tool.flext.workspace] attached = true`` and it is not already
        registered as a workspace submodule. Project-shape validation stays in
        ``_looks_like_project`` downstream; this helper only surfaces the
        explicit opt-in names.
        """
        workspace_submodule_names = (
            FlextInfraUtilitiesGitScope.git_tracked_top_level_dir_names(scope_root)
            or frozenset()
        )
        attached: list[str] = []
        for entry in sorted(scope_root.iterdir(), key=lambda item: item.name):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            if entry.name in workspace_submodule_names:
                continue
            if not (entry / c.Infra.PYPROJECT_FILENAME).is_file():
                continue
            try:
                if u.read_tool_flext_config(entry).workspace.attached:
                    attached.append(entry.name)
            except (FileNotFoundError, ValueError):
                continue
        return frozenset(attached)

    @staticmethod
    def discover_project_candidates(
        workspace_root: Path,
        *,
        scan_dirs: frozenset[str] | None = None,
        include_attached: bool = False,
    ) -> t.SequenceOf[Path]:
        """Return all canonical project candidates before any consumer-specific filtering.

        When ``include_attached`` is True, external sub-repos at workspace
        top-level (git repos with their own ``pyproject.toml`` not registered
        in the workspace submodule index) are surfaced alongside the
        git-tracked dirs of ``workspace_root``. Discovery is purely structural
        — no name patterns or hardcoded project lists. Default (False)
        preserves workspace-submodule-only enumeration.
        """
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
            FlextInfraUtilitiesProjectDiscovery._attached_top_level_dir_names(
                resolved_workspace_root,
            )
            if include_attached
            else frozenset()
        )

        if FlextInfraUtilitiesProjectDiscovery._looks_like_project(
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
                and (not entry.name.startswith("."))
                and (
                    entry.name in attached_child_dirs
                    or FlextInfraUtilitiesGitScope.project_descriptor_is_tracked(
                        resolved_workspace_root,
                        entry.resolve(),
                    )
                )
                and FlextInfraUtilitiesProjectDiscovery._looks_like_project(
                    entry.resolve(),
                    effective_scan_dirs=effective_scan_dirs,
                    configured_member_set=configured_member_set,
                )
            ],
        )
        if not roots and (resolved_workspace_root / c.Infra.DEFAULT_SRC_DIR).is_dir():
            return [resolved_workspace_root]
        return roots


__all__: list[str] = ["FlextInfraUtilitiesProjectDiscovery"]
