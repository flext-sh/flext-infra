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
from typing import override

from flext_core import r
from flext_infra.base import s
from flext_infra.codegen._lazy_init_generation import (
    FlextInfraCodegenLazyInitGenerationMixin,
)
from flext_infra.codegen.lazy_init_planner import FlextInfraCodegenLazyInitPlanner
from flext_infra.constants import c
from flext_infra.protocols import p
from flext_infra.typings import t
from flext_infra.utilities import u
from flext_infra.workspace.rope import FlextInfraRopeWorkspace


class FlextInfraCodegenLazyInit(s[bool], FlextInfraCodegenLazyInitGenerationMixin):
    """Generates ``__init__.py`` with PEP 562 lazy imports.

    Scans sibling ``.py`` files in each package directory, discovers their
    exports, and generates clean lazy-loading ``__init__.py`` files.
    Processes bottom-up so child packages are generated before parents.
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
        errors = self.generate_inits(check_only=self.check_only)
        if self._duplicate_class_names > 0:
            return r[bool].fail(
                f"init aborted: {self._duplicate_class_names} "
                "duplicate class name(s) detected (see errors above); "
                "rename one side before regenerating",
            )
        if errors > 0:
            return r[bool].fail(f"init failed in {errors} package directories")
        return r[bool].ok(True)

    def generate_inits(self, *, check_only: bool = False) -> int:
        """Process all package directories bottom-up and generate PEP 562 inits."""
        self._modified_files.clear()
        if not self.workspace_root.exists():
            u.Cli.info("Lazy-init summary: 0 generated, 0 errors (0 dirs scanned)")
            return 0
        started_at = perf_counter()
        u.Cli.info(
            "lazy-init: starting "
            f"({'check' if check_only else 'apply'}) for {self.workspace_root}",
        )
        lazy_init = u.Infra.load_tool_config().unwrap().lazy_init
        with FlextInfraRopeWorkspace.open_workspace(self.workspace_root) as rope:
            duplicates = self._detect_duplicate_class_names(rope)
            if duplicates:
                self._duplicate_class_names = len(duplicates)
                for class_name, locations in duplicates.items():
                    joined = ", ".join(locations)
                    u.Cli.error(
                        f"duplicate class name {class_name!r} in: {joined}; "
                        "rename one before regenerating __init__.py",
                    )
                u.Cli.info(
                    "Lazy-init summary: 0 generated, "
                    f"{len(duplicates)} duplicate class name(s) "
                    "(aborted before codegen)",
                )
                return len(duplicates)
            planner = FlextInfraCodegenLazyInitPlanner(
                rope_workspace=rope,
                lazy_init=lazy_init,
            )
            package_dirs = sorted(
                (
                    package_dir
                    for package_dir in rope.workspace_index.package_dirs
                    if package_dir.is_relative_to(self.workspace_root.resolve())
                ),
                key=lambda path: len(path.parts),
                reverse=True,
            )
            u.Cli.info(
                f"lazy-init: planning {len(package_dirs)} package dirs",
            )
            total, ok, errors, _dir_exports = self._generate_all_inits(
                package_dirs,
                check_only=check_only,
                planner=planner,
            )
        warnings = planner.collision_count
        u.Cli.info(
            f"Lazy-init summary: {ok} generated, {errors} errors, {warnings} warnings"
            f" ({total} dirs scanned, {perf_counter() - started_at:.2f}s)",
        )
        return errors

    @staticmethod
    def _detect_duplicate_class_names(
        rope: FlextInfraRopeWorkspace,
    ) -> t.MappingKV[str, t.StrSequence]:
        """Return class-name collisions.

        Scope rules:
        - ``src/`` modules: duplicates forbidden across the entire workspace.
        - ``tests/``/``scripts/``/``examples/``/``docs/`` modules: duplicates
          forbidden only within the same owning project (they do not escape).
        """
        scoped_modules: defaultdict[t.StrPair, set[str]] = defaultdict(set)
        for entry in rope.workspace_index.modules_by_path.values():
            if entry.is_package_init or not entry.module_name:
                continue
            module_segments = frozenset(entry.module_name.split("."))
            is_private_scope = bool(module_segments & c.Infra.NON_PUBLIC_LAZY_ROOTS)
            scope_key = (
                str(entry.project_root)
                if is_private_scope and entry.project_root is not None
                else ""
            )
            for obj in rope.objects(
                entry.file_path,
                include_local_scopes=False,
                include_references=False,
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
            else f"[workspace] {name}": tuple(
                sorted(modules),
            )
            for (name, scope_key), modules in scoped_modules.items()
            if len(modules) > 1
        }


__all__: list[str] = ["FlextInfraCodegenLazyInit"]
