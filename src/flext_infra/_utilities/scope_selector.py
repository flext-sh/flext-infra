"""Scope selector helper for flext-infra refactor verbs (Lane A-CH Task 0.4).

Resolves a target selector (``--module``, ``--namespace``, ``--project``,
``--projects``, ``--files``, or workspace default) into a typed
``m.Infra.ScopeResolution``. Consumed by every refactor verb dispatcher so
file-level operations always receive a sorted, deduplicated, in-workspace
file list.

Per AGENT_COORDINATION.md §2.2 + §4.2, A-CH owns this surface; A-TS / A-PT /
A-HD consume it without redefining.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_core.result import FlextResult

from flext_infra import c
from flext_infra._models.scope import FlextInfraModelsScope


class FlextInfraUtilitiesScopeSelector:
    """Resolve scope selectors into a typed ``m.Infra.ScopeResolution``."""

    _NAMESPACE_ALIASES: frozenset[str] = frozenset({
        "c",
        "m",
        "p",
        "t",
        "u",
        "r",
        "e",
        "h",
        "s",
        "x",
        "d",
    })

    @staticmethod
    def scope_resolve(
        *,
        workspace_root: Path,
        module: str | None = None,
        namespace: str | None = None,
        project: str | None = None,
        projects: Sequence[str] | None = None,
        files: Sequence[Path] | None = None,
    ) -> FlextResult[FlextInfraModelsScope.ScopeResolution]:
        """Resolve a selector to a typed scope resolution.

        Exactly one of ``module``, ``namespace``, ``project``, ``projects``,
        ``files`` is interpreted (in that priority order). When none is
        provided, level is ``WORKSPACE``.
        """
        try:
            workspace_resolved = workspace_root.resolve()
        except OSError as exc:
            return FlextResult[FlextInfraModelsScope.ScopeResolution].fail(
                f"workspace_root not resolvable: {exc}",
            )

        if module is not None:
            return FlextInfraUtilitiesScopeSelector._resolve_module(
                workspace_resolved, module
            )
        if namespace is not None:
            return FlextInfraUtilitiesScopeSelector._resolve_namespace(
                workspace_resolved, namespace
            )
        if files:
            return FlextInfraUtilitiesScopeSelector._resolve_files(
                workspace_resolved, files
            )
        if projects:
            return FlextInfraUtilitiesScopeSelector._resolve_projects(
                workspace_resolved, projects
            )
        if project is not None:
            return FlextInfraUtilitiesScopeSelector._resolve_projects(
                workspace_resolved, (project,), single=True
            )
        return FlextResult[FlextInfraModelsScope.ScopeResolution].ok(
            FlextInfraModelsScope.ScopeResolution(
                level=c.Infra.ScopeLevel.WORKSPACE,
                workspace_root=workspace_resolved,
            )
        )

    @staticmethod
    def _resolve_module(
        workspace_root: Path, module: str
    ) -> FlextResult[FlextInfraModelsScope.ScopeResolution]:
        if not module or "/" in module or module.startswith("."):
            return FlextResult[FlextInfraModelsScope.ScopeResolution].fail(
                f"invalid dotted module path: {module!r}",
            )
        parts = module.split(".")
        candidate_paths: list[Path] = []
        # Look in each project's src/ tree for matching .py file
        for project_dir in sorted(workspace_root.glob("flext-*")):
            src_root = project_dir / "src"
            if not src_root.exists():
                continue
            module_file = src_root.joinpath(*parts).with_suffix(".py")
            if module_file.exists() and module_file.is_relative_to(workspace_root):
                candidate_paths.append(module_file)
        # If module path is "flext_core._models.enforcement", also try the
        # explicit project layout under workspace_root/<project>/src.
        if not candidate_paths:
            module_root = parts[0].replace("_", "-")
            direct = workspace_root.joinpath(module_root, "src", *parts).with_suffix(
                ".py"
            )
            if direct.exists() and direct.is_relative_to(workspace_root):
                candidate_paths.append(direct)
        if not candidate_paths:
            return FlextResult[FlextInfraModelsScope.ScopeResolution].fail(
                f"module not found in workspace: {module!r}",
            )
        return FlextResult[FlextInfraModelsScope.ScopeResolution].ok(
            FlextInfraModelsScope.ScopeResolution(
                level=c.Infra.ScopeLevel.MODULE,
                workspace_root=workspace_root,
                module=module,
                files=tuple(sorted(set(candidate_paths))),
            )
        )

    @staticmethod
    def _resolve_namespace(
        workspace_root: Path, namespace: str
    ) -> FlextResult[FlextInfraModelsScope.ScopeResolution]:
        parts = namespace.split(".")
        alias = parts[0]
        if alias not in FlextInfraUtilitiesScopeSelector._NAMESPACE_ALIASES:
            return FlextResult[FlextInfraModelsScope.ScopeResolution].fail(
                f"unknown namespace alias: {alias!r}; expected one of "
                f"{sorted(FlextInfraUtilitiesScopeSelector._NAMESPACE_ALIASES)}",
            )
        path_segments = tuple(parts[1:])
        return FlextResult[FlextInfraModelsScope.ScopeResolution].ok(
            FlextInfraModelsScope.ScopeResolution(
                level=c.Infra.ScopeLevel.NAMESPACE,
                workspace_root=workspace_root,
                namespace_alias=alias,
                namespace_path=path_segments,
            )
        )

    @staticmethod
    def _resolve_files(
        workspace_root: Path, files: Sequence[Path]
    ) -> FlextResult[FlextInfraModelsScope.ScopeResolution]:
        absolute_files: list[Path] = []
        for raw in files:
            try:
                resolved = (workspace_root / raw).resolve()
            except OSError as exc:
                return FlextResult[FlextInfraModelsScope.ScopeResolution].fail(
                    f"failed to resolve file {raw!r}: {exc}",
                )
            if not resolved.is_relative_to(workspace_root):
                return FlextResult[FlextInfraModelsScope.ScopeResolution].fail(
                    f"file escapes workspace: {raw!r} → {resolved}",
                )
            absolute_files.append(resolved)
        return FlextResult[FlextInfraModelsScope.ScopeResolution].ok(
            FlextInfraModelsScope.ScopeResolution(
                level=c.Infra.ScopeLevel.FILES,
                workspace_root=workspace_root,
                files=tuple(sorted(set(absolute_files))),
            )
        )

    @staticmethod
    def _resolve_projects(
        workspace_root: Path,
        projects: Sequence[str],
        *,
        single: bool = False,
    ) -> FlextResult[FlextInfraModelsScope.ScopeResolution]:
        names: list[str] = []
        for name in projects:
            if not name or "/" in name or name.startswith("."):
                return FlextResult[FlextInfraModelsScope.ScopeResolution].fail(
                    f"invalid project name: {name!r}",
                )
            project_dir = workspace_root / name
            if (
                not project_dir.exists()
                or not (project_dir / "pyproject.toml").exists()
            ):
                return FlextResult[FlextInfraModelsScope.ScopeResolution].fail(
                    f"project not found in workspace: {name!r}",
                )
            names.append(name)
        return FlextResult[FlextInfraModelsScope.ScopeResolution].ok(
            FlextInfraModelsScope.ScopeResolution(
                level=(
                    c.Infra.ScopeLevel.PROJECT
                    if single
                    else c.Infra.ScopeLevel.PROJECTS
                ),
                workspace_root=workspace_root,
                projects=tuple(sorted(set(names))),
            )
        )


__all__: list[str] = ["FlextInfraUtilitiesScopeSelector"]
