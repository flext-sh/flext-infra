"""Scope selector helper — turns CLI selectors into a typed file universe.

The single ``scope_resolve`` classmethod dispatches on the first non-None
selector (files / module / namespace / project / projects) and falls back
to WORKSPACE. Project, projects and workspace levels reuse
``FlextInfraUtilitiesIteration.iter_python_files`` /
``FlextInfraUtilitiesDocsScope.resolve_projects`` — no project-discovery or
file-walking logic is duplicated here.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_core import FlextProtocols as p, FlextResult as r

from flext_infra._constants.base import FlextInfraConstantsBase as c
from flext_infra._models.scope import FlextInfraModelsScope
from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration


class FlextInfraUtilitiesScopeSelector:
    """Resolve CLI scope selectors into a typed ``FlextInfraModelsScope.ScopeResolution``."""

    @classmethod
    def scope_resolve(
        cls,
        *,
        workspace_root: Path,
        module: str | None = None,
        namespace: str | None = None,
        project: str | None = None,
        projects: Sequence[str] | None = None,
        files: Sequence[Path] | None = None,
    ) -> p.Result[FlextInfraModelsScope.ScopeResolution]:
        """Dispatch on the first non-None selector and build the resolution.

        Selector precedence (mirrors AGENTS.md §5 narrowing rules):
        ``files`` → ``module`` → ``namespace`` → ``projects`` →
        ``project`` → workspace fallback.
        """
        resolved_root = workspace_root.resolve()
        if files is not None:
            return cls._resolve_files(resolved_root, files)
        if module is not None:
            return cls._resolve_module(resolved_root, module)
        if namespace is not None:
            return cls._resolve_namespace(resolved_root, namespace, project)
        if projects is not None:
            return cls._resolve_projects(resolved_root, projects, c.ScopeLevel.PROJECTS)
        if project is not None:
            return cls._resolve_projects(
                resolved_root, (project,), c.ScopeLevel.PROJECT
            )
        return cls._resolve_workspace(resolved_root)

    @staticmethod
    def _build(
        level: c.ScopeLevel,
        workspace_root: Path,
        files: Sequence[Path],
    ) -> p.Result[FlextInfraModelsScope.ScopeResolution]:
        normalized = tuple(sorted({file.resolve() for file in files}))
        return r[FlextInfraModelsScope.ScopeResolution].ok(
            FlextInfraModelsScope.ScopeResolution(
                level=level,
                workspace_root=workspace_root,
                files=normalized,
            ),
        )

    @classmethod
    def _resolve_workspace(
        cls, workspace_root: Path
    ) -> p.Result[FlextInfraModelsScope.ScopeResolution]:
        files_result = FlextInfraUtilitiesIteration.iter_python_files(
            workspace_root,
        )
        if files_result.failure:
            return r[FlextInfraModelsScope.ScopeResolution].fail(
                files_result.error or "iter_python_files failed",
            )
        return cls._build(c.ScopeLevel.WORKSPACE, workspace_root, files_result.value)

    @classmethod
    def _resolve_named_project_paths(
        cls, workspace_root: Path, names: Sequence[str]
    ) -> p.Result[tuple[Path, ...]]:
        """Map project names to their on-disk roots, failing on unknown names."""
        candidates = FlextInfraUtilitiesIteration.discover_project_candidates(
            workspace_root,
        )
        by_name: dict[str, Path] = {}
        for candidate in candidates:
            by_name[candidate.name] = candidate
            by_name[candidate.name.replace("-", "_")] = candidate
        missing = sorted(set(names) - by_name.keys())
        if missing:
            return r[tuple[Path, ...]].fail(
                f"unknown projects: {', '.join(missing)}",
            )
        return r[tuple[Path, ...]].ok(tuple(by_name[name] for name in names))

    @classmethod
    def _resolve_projects(
        cls,
        workspace_root: Path,
        names: Sequence[str],
        level: c.ScopeLevel,
    ) -> p.Result[FlextInfraModelsScope.ScopeResolution]:
        roots_result = cls._resolve_named_project_paths(workspace_root, names)
        if roots_result.failure:
            return r[FlextInfraModelsScope.ScopeResolution].fail(
                roots_result.error or "project resolution failed",
            )
        files_result = FlextInfraUtilitiesIteration.iter_python_files(
            workspace_root,
            project_roots=roots_result.value,
        )
        if files_result.failure:
            return r[FlextInfraModelsScope.ScopeResolution].fail(
                files_result.error or "iter_python_files failed",
            )
        return cls._build(level, workspace_root, files_result.value)

    @classmethod
    def _resolve_files(
        cls, workspace_root: Path, files: Sequence[Path]
    ) -> p.Result[FlextInfraModelsScope.ScopeResolution]:
        outside: list[str] = []
        for file in files:
            resolved = file.resolve()
            if not resolved.is_relative_to(workspace_root):
                outside.append(str(resolved))
        if outside:
            joined = ", ".join(sorted(outside))
            return r[FlextInfraModelsScope.ScopeResolution].fail(
                f"files outside workspace_root: {joined}",
            )
        return cls._build(c.ScopeLevel.FILES, workspace_root, files)

    @classmethod
    def _resolve_module(
        cls, workspace_root: Path, module: str
    ) -> p.Result[FlextInfraModelsScope.ScopeResolution]:
        # Walk every project candidate and translate the dotted module path
        # to ``<project>/src/<segment_0>/<segment_1>...py``. Stop at the
        # first match — module names are unique across the workspace by the
        # canonical-facade contract.
        segments = module.split(".")
        if not segments or any(not segment for segment in segments):
            return r[FlextInfraModelsScope.ScopeResolution].fail(
                f"invalid module path: {module!r}",
            )
        for project_root in FlextInfraUtilitiesIteration.discover_project_candidates(
            workspace_root,
        ):
            candidate = project_root / "src" / Path(*segments).with_suffix(".py")
            if candidate.exists():
                return cls._build(c.ScopeLevel.MODULE, workspace_root, (candidate,))
        return r[FlextInfraModelsScope.ScopeResolution].fail(
            f"module not found in workspace: {module!r}",
        )

    @classmethod
    def _resolve_namespace(
        cls,
        workspace_root: Path,
        namespace: str,
        project: str | None,
    ) -> p.Result[FlextInfraModelsScope.ScopeResolution]:
        canonical = c.NAMESPACE_TO_CANONICAL_FILENAME.get(namespace)
        if canonical is None:
            allowed = ", ".join(sorted(c.NAMESPACE_TO_CANONICAL_FILENAME))
            return r[FlextInfraModelsScope.ScopeResolution].fail(
                f"unknown namespace alias {namespace!r}; expected one of: {allowed}",
            )
        if project is None:
            project_roots: Sequence[Path] = (
                FlextInfraUtilitiesIteration.discover_project_candidates(
                    workspace_root,
                )
            )
        else:
            roots_result = cls._resolve_named_project_paths(workspace_root, (project,))
            if roots_result.failure:
                return r[FlextInfraModelsScope.ScopeResolution].fail(
                    roots_result.error or "project resolution failed",
                )
            project_roots = roots_result.value
        matches = [
            src_path
            for project_root in project_roots
            for src_path in (project_root / "src").rglob(canonical)
        ]
        return cls._build(c.ScopeLevel.NAMESPACE, workspace_root, matches)
