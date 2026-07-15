"""Canonical ``__init__.py`` generator for complete Python workspaces.

Auto-discovers exports from sibling ``.py`` files. Every governed surface root
uses PEP 562; descendant packages use explicit static reexports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from time import perf_counter
from typing import override

from flext_core import r
from flext_infra import c, config, p, t, u
from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase
from flext_infra.codegen._lazy_init_generation import (
    FlextInfraCodegenLazyInitGenerationMixin,
)
from flext_infra.codegen.lazy_init_planner import FlextInfraCodegenLazyInitPlanner
from flext_infra.workspace.rope import FlextInfraRopeWorkspace


class FlextInfraCodegenLazyInit(
    FlextInfraProjectSelectionServiceBase[bool],
    FlextInfraCodegenLazyInitGenerationMixin,
):
    """Generate canonical root and subpackage ``__init__.py`` files.

    Production and wrapper roots use PEP 562 lazy exports. Descendants use
    static sibling-relative reexports at every depth. Processing is bottom-up
    so each package plan receives complete child export information.
    """

    _modified_files: t.Infra.StrSet = u.PrivateAttr(default_factory=set)
    _duplicate_class_names: int = u.PrivateAttr(default_factory=lambda: 0)

    @property
    def modified_files(self) -> t.StrSequence:
        """Generated __init__.py files that changed on disk."""
        return tuple(sorted(self._modified_files))

    @override
    def execute(self) -> p.Result[bool]:
        """Execute lazy-init directly from the validated CLI service model."""
        # NOTE (multi-agent, mro-wkii.17.15): one normalized mode controls every write.
        effective_dry_run = self.effective_dry_run
        errors = self.generate_inits(check_only=effective_dry_run)
        if self._duplicate_class_names > 0:
            return r[bool].fail(
                f"init aborted: {self._duplicate_class_names} "
                "duplicate class name(s) detected (see errors above); "
                "rename one side before regenerating"
            )
        if errors > 0:
            return r[bool].fail(f"init failed in {errors} package directories")
        if effective_dry_run and self._modified_files:
            return r[bool].fail(
                "init drift detected in "
                f"{len(self._modified_files)} generated artifacts"
            )
        return r[bool].ok(True)

    def generate_inits(self, *, check_only: bool = False) -> int:
        """Generate each selected public root and its subpackages bottom-up."""
        self._modified_files.clear()
        self._duplicate_class_names = 0
        if not self.workspace_root.exists():
            u.Cli.info("Lazy-init summary: 0 generated, 0 errors (0 dirs scanned)")
            return 0
        started_at = perf_counter()
        u.Cli.info(
            "lazy-init: starting "
            f"({'check' if check_only else 'apply'}) for {self.workspace_root}"
        )
        lazy_init = config.Infra.tooling.lazy_init
        with FlextInfraRopeWorkspace.open_workspace(self.workspace_root) as rope:
            workspace_index = rope.workspace_index
            resolved_workspace_root = self.workspace_root.resolve()
            # NOTE(mro-wkii.17.26, agent codex): index every package depth once;
            # rendering alone decides whether a package is the public lazy root.
            indexed_package_dirs = tuple(
                sorted(
                    frozenset(
                        package_dir.resolve()
                        for package_dir in workspace_index.package_dirs
                        if package_dir.is_relative_to(resolved_workspace_root)
                    ),
                    key=lambda path: len(path.parts),
                    reverse=True,
                )
            )
            selected_project_names = frozenset(self.project_names or ())
            indexed_project_names = frozenset(
                entry.project_root.name
                for entry in workspace_index.packages_by_dir.values()
                if entry.project_root is not None
            )
            missing_project_names = selected_project_names - indexed_project_names
            if missing_project_names:
                u.Cli.error(
                    "lazy-init selected project not found: "
                    + ", ".join(sorted(missing_project_names))
                )
                return 1
            package_dirs = tuple(
                package_dir
                for package_dir in indexed_package_dirs
                if not selected_project_names
                or (
                    (
                        package_entry := workspace_index.packages_by_dir.get(
                            str(package_dir)
                        )
                    )
                    is not None
                    and package_entry.project_root is not None
                    and package_entry.project_root.name in selected_project_names
                )
            )
            target_package_dir: Path | None = None
            target_includes_descendants = False
            if self.target_module:
                # mro-wkii.17.26 (codex): reuse the canonical workspace project
                # selector instead of exposing the legacy internal filter field.
                mapped_package_dir = workspace_index.package_dir_by_name.get(
                    self.target_module
                )
                target_module_dirs = frozenset(
                    entry.package_dir.resolve()
                    for entry in workspace_index.modules_by_path.values()
                    if entry.module_name == self.target_module
                    and (
                        not selected_project_names
                        or (
                            entry.project_root is not None
                            and entry.project_root.name in selected_project_names
                        )
                    )
                )
                mapped_package = (
                    workspace_index.packages_by_dir.get(
                        str(mapped_package_dir.resolve())
                    )
                    if mapped_package_dir is not None
                    else None
                )
                if mapped_package_dir is not None and (
                    not selected_project_names
                    or (
                        mapped_package is not None
                        and mapped_package.project_root is not None
                        and mapped_package.project_root.name in selected_project_names
                    )
                ):
                    # mro-wkii.17.26 (Codex): --projects qualifies repeated
                    # wrapper module names before ambiguity is evaluated.
                    target_module_dirs = frozenset((
                        *target_module_dirs,
                        mapped_package_dir.resolve(),
                    ))
                sorted_target_dirs = tuple(sorted(target_module_dirs))
                if not sorted_target_dirs:
                    u.Cli.error(
                        f"lazy-init target module not found: {self.target_module}"
                    )
                    return 1
                if sorted_target_dirs[1:]:
                    u.Cli.error(
                        f"lazy-init target module is ambiguous: {self.target_module}"
                    )
                    return 1
                target_package_dir = sorted_target_dirs[0]
            if target_package_dir is not None:
                target_parts = target_package_dir.relative_to(
                    resolved_workspace_root
                ).parts
                boundary_names = frozenset({
                    c.Infra.DEFAULT_SRC_DIR,
                    *lazy_init.surface_prefixes,
                })
                boundary_index = next(
                    (
                        index
                        for index, part in enumerate(target_parts)
                        if part in boundary_names
                    ),
                    len(target_parts) - 1,
                )
                scope_prefix = target_parts[: boundary_index + 1]
                project_prefix = target_parts[:boundary_index]
                production_prefix = (*project_prefix, c.Infra.DEFAULT_SRC_DIR)
                # mro-wkii.17.26.2 (codex): roots own a recursive surface;
                # nested targets are exact so surgical regeneration cannot
                # rewrite unrelated descendant initializer drift.
                target_includes_descendants = (
                    target_parts[boundary_index] == c.Infra.DEFAULT_SRC_DIR
                    and len(target_parts) == boundary_index + 2
                ) or len(target_parts) == boundary_index + 1
                package_dirs = tuple(
                    package_dir
                    for package_dir in indexed_package_dirs
                    if (
                        package_dir.relative_to(resolved_workspace_root).parts[
                            : len(scope_prefix)
                        ]
                        == scope_prefix
                        # mro-pulj (codex): wrapper aliases depend on the same
                        # project's production plans, consumed read-only.
                        or package_dir.relative_to(resolved_workspace_root).parts[
                            : len(production_prefix)
                        ]
                        == production_prefix
                    )
                )
            duplicates = self._detect_duplicate_class_names(
                rope, package_dirs=package_dirs
            )
            if duplicates:
                self._duplicate_class_names = len(duplicates)
                for class_name, locations in duplicates.items():
                    joined = ", ".join(locations)
                    u.Cli.error(
                        f"duplicate class name {class_name!r} in: {joined}; "
                        "rename one before regenerating __init__.py"
                    )
                u.Cli.info(
                    "Lazy-init summary: 0 generated, "
                    f"{len(duplicates)} duplicate class name(s) "
                    "(aborted before codegen)"
                )
                return len(duplicates)
            planner = FlextInfraCodegenLazyInitPlanner(
                rope_workspace=rope, lazy_init=lazy_init
            )
            u.Cli.info(f"lazy-init: planning {len(package_dirs)} package dirs")
            total, ok, errors, _dir_exports = self._generate_all_inits(
                package_dirs,
                check_only=check_only,
                planner=planner,
                target_package_dir=target_package_dir,
                target_includes_descendants=target_includes_descendants,
            )
        u.Cli.info(
            f"Lazy-init summary: {ok} generated, {errors} errors "
            f"({total} dirs scanned, {perf_counter() - started_at:.2f}s)"
        )
        return errors

    @staticmethod
    def _detect_duplicate_class_names(
        rope: FlextInfraRopeWorkspace, *, package_dirs: t.SequenceOf[Path]
    ) -> t.MappingKV[str, t.StrSequence]:
        """Return class-name collisions.

        Scope rules:
        - ``src/`` modules: duplicates forbidden across the entire workspace.
        - ``tests/``/``scripts/``/``examples/``/``docs/`` modules: duplicates
          forbidden only within the same owning project (they do not escape).
        """
        scoped_modules: defaultdict[t.StrPair, set[str]] = defaultdict(set)
        selected_package_dirs = frozenset(path.resolve() for path in package_dirs)
        # mro-wkii.17.26 (codex): validated config is the sole wrapper inventory.
        wrapper_surface_roots = frozenset(
            config.Infra.tooling.lazy_init.surface_prefixes
        )
        for entry in rope.workspace_index.modules_by_path.values():
            if (
                entry.package_dir.resolve() not in selected_package_dirs
                or entry.is_package_init
                or not entry.module_name
            ):
                continue
            module_segments = frozenset(entry.module_name.split("."))
            is_private_scope = bool(module_segments & wrapper_surface_roots)
            scope_key = (
                str(entry.project_root)
                if is_private_scope and entry.project_root is not None
                else ""
            )
            for obj in rope.objects(
                entry.file_path, include_local_scopes=False, include_references=False
            ):
                if obj.kind != "class" or obj.scope_path:
                    continue
                name = obj.name
                if len(name) < c.Infra.DUPLICATE_CLASS_MIN_LEN or not name[0].isupper():
                    continue
                scoped_modules[name, scope_key].add(entry.module_name)
        return {
            f"[{Path(scope_key).name}] {name}"
            if scope_key
            else f"[workspace] {name}": tuple(sorted(modules))
            for (name, scope_key), modules in scoped_modules.items()
            if len(modules) > 1
        }


__all__: list[str] = ["FlextInfraCodegenLazyInit"]
