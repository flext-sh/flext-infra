"""Lazy-init ``__init__.py`` generator (PEP 562).

Auto-discovers exports from sibling ``.py`` files and generates clean
lazy-loading ``__init__.py`` files using ``flext_core``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING, override

from flext_core import r
from flext_infra import c, config, u
from flext_infra.base import s
from flext_infra.codegen._lazy_init_generation import (
    FlextInfraCodegenLazyInitGenerationMixin,
)
from flext_infra.codegen.lazy_init_planner import FlextInfraCodegenLazyInitPlanner
from flext_infra.workspace.rope import FlextInfraRopeWorkspace

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraCodegenLazyInit(s[bool], FlextInfraCodegenLazyInitGenerationMixin):
    """Generate canonical root and subpackage ``__init__.py`` files.

    Public package roots use PEP 562 lazy exports. Descendant packages use
    static sibling-relative reexports or remain empty. Processing is bottom-up
    so the root plan receives complete child export information.
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
                f"init drift detected in {len(self._modified_files)} generated artifacts"
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
            # NOTE(mro-wkii.17.26, agent codex): lazy exports exist only at public src roots.
            public_package_dirs = frozenset(
                package_dir.resolve()
                for package_dir in workspace_index.package_dirs
                if package_dir.is_relative_to(resolved_workspace_root)
                and package_dir.parent.name == c.Infra.DEFAULT_SRC_DIR
                and (package_dir.parent.parent / c.Infra.PYPROJECT_FILENAME).is_file()
            )
            package_dirs = tuple(
                sorted(
                    (
                        package_dir.resolve()
                        for package_dir in workspace_index.package_dirs
                        if package_dir.is_relative_to(resolved_workspace_root)
                        and any(
                            package_dir.resolve() == public_root
                            or public_root in package_dir.resolve().parents
                            for public_root in public_package_dirs
                        )
                    ),
                    key=lambda path: len(path.parts),
                    reverse=True,
                )
            )
            if self.target_module:
                mapped_package_dir = workspace_index.package_dir_by_name.get(
                    self.target_module
                )
                target_module_dirs = frozenset(
                    entry.package_dir.resolve()
                    for entry in workspace_index.modules_by_path.values()
                    if entry.module_name == self.target_module
                )
                if mapped_package_dir is not None:
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
                if sorted_target_dirs[0] not in public_package_dirs:
                    u.Cli.error(
                        "lazy-init target must be a public src package root: "
                        f"{self.target_module}"
                    )
                    return 1
                selected_root = sorted_target_dirs[0]
                package_dirs = tuple(
                    package_dir
                    for package_dir in package_dirs
                    if package_dir == selected_root or selected_root in package_dir.parents
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
                package_dirs, check_only=check_only, planner=planner
            )
        warnings = planner.collision_count
        u.Cli.info(
            f"Lazy-init summary: {ok} generated, {errors} errors, {warnings} warnings"
            f" ({total} dirs scanned, {perf_counter() - started_at:.2f}s)"
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
        for entry in rope.workspace_index.modules_by_path.values():
            if (
                entry.package_dir.resolve() not in selected_package_dirs
                or entry.is_package_init
                or not entry.module_name
            ):
                continue
            module_segments = frozenset(entry.module_name.split("."))
            is_private_scope = bool(module_segments & c.Infra.NON_PUBLIC_LAZY_ROOTS)
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
