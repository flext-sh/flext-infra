"""Workspace Python module iteration mixin.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import p, r, t
from flext_infra._iteration_workspace import FlextInfraUtilitiesIterationWorkspace
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery


class FlextInfraUtilitiesIterationModules:
    """Static helpers for discovering (project_root, file_path) module tuples."""

    @staticmethod
    def iter_workspace_python_modules(
        workspace_root: Path,
        *,
        exclude_packages: frozenset[str] | None = None,
        include_tests: bool = True,
    ) -> p.Result[t.SequenceOf[t.Pair[Path, Path]]]:
        """Discover all Python modules across workspace projects.

        Returns tuples of (project_root, file_path) for every Python file
        found in the workspace. Optionally excludes packages by name and
        can skip test directories.

        Args:
            workspace_root: Root directory of the workspace.
            exclude_packages: Project directory names to exclude.
            include_tests: Whether to include files under tests/ dirs.

        Returns:
            Result containing list of (project_root, file_path) tuples.

        """
        try:
            result = (
                FlextInfraUtilitiesIterationModules._collect_workspace_python_modules(
                    workspace_root=workspace_root,
                    exclude_packages=exclude_packages,
                    include_tests=include_tests,
                )
            )
            return r[t.SequenceOf[t.Pair[Path, Path]]].ok(result)
        except OSError as exc:
            return r[t.SequenceOf[t.Pair[Path, Path]]].fail_op(
                "workspace python module iteration", exc
            )

    @staticmethod
    def _collect_workspace_python_modules(
        workspace_root: Path,
        exclude_packages: frozenset[str] | None,
        *,
        include_tests: bool,
    ) -> t.SequenceOf[t.Pair[Path, Path]]:
        """Collect (project_root, file_path) tuples across workspace projects."""
        roots = FlextInfraUtilitiesProjectDiscovery.discover_project_roots(
            workspace_root=workspace_root,
        )
        effective_exclude = exclude_packages or frozenset()
        result: t.MutableSequenceOf[t.Pair[Path, Path]] = []
        for project_root in roots:
            if project_root.name in effective_exclude:
                continue
            files_result = FlextInfraUtilitiesIterationWorkspace.iter_python_files(
                workspace_root=workspace_root,
                project_roots=[project_root],
                include_tests=include_tests,
            )
            if files_result.failure:
                continue
            result.extend((project_root, file_path) for file_path in files_result.value)
        return result


__all__: list[str] = ["FlextInfraUtilitiesIterationModules"]
