"""Project discovery helpers for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from operator import attrgetter
from pathlib import Path

from flext_infra import config, m
from flext_infra.constants import c
from flext_infra.typings import t

from ._project_discovery_candidates import (
    FlextInfraUtilitiesProjectDiscoveryCandidatesMixin,
)
from .git import FlextInfraUtilitiesGit


class FlextInfraUtilitiesProjectDiscovery(
    FlextInfraUtilitiesProjectDiscoveryCandidatesMixin
):
    """Static helpers for discovering governed project roots in a workspace."""

    @classmethod
    def discover_project_roots(
        cls, repository_root: Path, *, scan_dirs: frozenset[str] | None = None
    ) -> t.SequenceOf[Path]:
        """Discover all project directories under repository root.

        Algorithm:
          1. Check if repository_root itself looks like a project
          2. Enumerate only projects declared by the root's own ``.gitmodules``.
          3. Return the root and declared projects in deterministic order.

        Args:
            repository_root: Root directory to start search from.
            scan_dirs: Directory names indicating a project exists (e.g., "src", "tests").
                Must be frozenset for use as constant. Defaults to standard project dirs.

        Returns:
            Project roots sorted by their ``.gitmodules`` declaration order.

        """
        declared_paths = FlextInfraUtilitiesGit.git_declared_submodule_paths(
            repository_root
        )
        if declared_paths.failure:
            raise ValueError(declared_paths.error or "invalid .gitmodules")
        configured_projects = tuple(path.as_posix() for path in declared_paths.value)
        candidates = cls.discover_project_candidates(
            repository_root, scan_dirs=scan_dirs
        )
        resolved_repository_root = repository_root.resolve()
        if not configured_projects:
            return candidates
        configured_order = {name: idx for idx, name in enumerate(configured_projects)}
        ordered: list[Path] = []

        def configured_key(candidate: Path) -> tuple[int, str]:
            relative = candidate.relative_to(resolved_repository_root).as_posix()
            return configured_order.get(
                relative, len(configured_projects)
            ), candidate.name

        non_root_candidates = sorted(
            (c for c in candidates if c != resolved_repository_root), key=configured_key
        )
        ordered.extend(non_root_candidates)
        return ordered

    @classmethod
    def discover_rope_project_roots(cls, repository_root: Path) -> t.SequenceOf[Path]:
        """Return every direct Python project sharing one Rope workspace root."""
        resolved_root = repository_root.resolve()
        declared = cls.discover_project_candidates(resolved_root)
        direct = tuple(
            child.resolve()
            for child in sorted(resolved_root.iterdir(), key=attrgetter("name"))
            if child.is_dir()
            and not child.name.startswith(".")
            and (child / c.Infra.PYPROJECT_FILENAME).is_file()
        )
        return tuple(sorted({*declared, *direct}, key=Path.as_posix))

    @classmethod
    def ast_grep_scan_targets(cls, repository_root: Path) -> t.StrSequence:
        """Return only governed handwritten Python surfaces as scan targets.

        A workspace root is not itself a Python source surface. Passing ``.`` to
        ast-grep also traverses generated agent hooks and other managed
        projections, so a project-local ``make mod`` could rewrite files owned by
        another generator. The refactor config is the single scope owner for
        source trees; root Python modules cover public entry points such as
        ``conftest.py`` without opening hidden directories.
        """
        resolved_root = repository_root.resolve()
        scan_dirs = m.Infra.RefactorConfig().project_scan_dirs
        targets = {
            target.relative_to(resolved_root).as_posix()
            for project in cls.governed_project_roots(resolved_root)
            for target in (
                *(project / directory for directory in scan_dirs),
                *project.glob(f"*{c.Infra.EXT_PYTHON}"),
            )
            if target.exists()
        }
        return tuple(sorted(targets))

    @classmethod
    def governed_project_roots(cls, repository_root: Path) -> t.SequenceOf[Path]:
        """Return the workspace root and each declared repository exactly once."""
        resolved_root = repository_root.resolve()
        return tuple(
            dict.fromkeys((
                resolved_root,
                *(
                    project.resolve()
                    for project in cls.discover_project_roots(resolved_root)
                ),
            ))
        )

    @staticmethod
    def external_tool_state_dir(
        workspace_root: Path, project_root: Path, tool_name: str
    ) -> Path:
        """Resolve one governed project's canonical state outside the checkout."""
        resolved_workspace = workspace_root.resolve()
        resolved_project = project_root.resolve()
        if not resolved_project.is_relative_to(resolved_workspace):
            msg = f"project root is outside workspace: {resolved_project}"
            raise ValueError(msg)
        tool_component = Path(tool_name)
        if (
            tool_component.is_absolute()
            or tool_component.name != tool_name
            or tool_name in {"", ".", ".."}
        ):
            msg = f"tool_name must be one relative directory name: {tool_name!r}"
            raise ValueError(msg)
        state_root = (
            resolved_workspace.parent
            / config.Infra.codegen.toolchain.state_directory_name
            / resolved_workspace.name
            / tool_name
        )
        relative_project = resolved_project.relative_to(resolved_workspace)
        return (
            state_root if relative_project == Path() else state_root / relative_project
        )


__all__: list[str] = ["FlextInfraUtilitiesProjectDiscovery"]
