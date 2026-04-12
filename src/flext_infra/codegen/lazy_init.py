"""Lazy-init ``__init__.py`` generator (PEP 562).

Auto-discovers exports from sibling ``.py`` files and generates clean
lazy-loading ``__init__.py`` files using ``flext_core.lazy``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import override

from pydantic import PrivateAttr

from flext_core import r
from flext_infra import (
    FlextInfraCodegenGeneration,
    FlextInfraServiceBase,
    c,
    m,
    t,
    u,
)
from flext_infra.codegen.lazy_init_planner import FlextInfraCodegenLazyInitPlanner


class FlextInfraCodegenLazyInit(FlextInfraServiceBase[bool]):
    """Generates ``__init__.py`` with PEP 562 lazy imports.

    Scans sibling ``.py`` files in each package directory, discovers their
    exports, and generates clean lazy-loading ``__init__.py`` files.
    Processes bottom-up so child packages are generated before parents.
    """

    _modified_files: t.Infra.StrSet = PrivateAttr()

    @override
    def model_post_init(self, __context: t.ScalarMapping | None, /) -> None:
        """Create private lazy-init state after model validation."""
        super().model_post_init(__context)
        self._modified_files = set()

    @property
    def modified_files(self) -> Sequence[str]:
        """Return generated __init__.py files that changed on disk."""
        return tuple(sorted(self._modified_files))

    @override
    def execute(self) -> r[bool]:
        """Execute lazy-init directly from the validated CLI service model."""
        errors = self.generate_inits(check_only=self.check_only)
        if errors > 0:
            return r[bool].fail(f"lazy-init failed in {errors} package directories")
        return r[bool].ok(True)

    def generate_inits(self, *, check_only: bool = False) -> int:
        """Process all package directories bottom-up and generate PEP 562 inits."""
        self._modified_files.clear()
        lazy_init = u.Infra.load_tool_config().unwrap().lazy_init
        rope_workspace_root = u.Infra.rope_workspace_root(self.workspace_root)
        with u.Infra.open_project(rope_workspace_root) as rope_project:
            workspace_index = u.Infra.index_rope_workspace(
                rope_project,
                rope_workspace_root,
            )
            planner = FlextInfraCodegenLazyInitPlanner(
                workspace_root=rope_workspace_root,
                rope_project=rope_project,
                workspace_index=workspace_index,
                lazy_init=lazy_init,
            )
            total, ok, errors, _dir_exports = self._generate_all_inits(
                sorted(
                    (
                        package_dir
                        for package_dir in workspace_index.package_dirs
                        if package_dir.is_relative_to(self.workspace_root.resolve())
                    ),
                    key=lambda path: len(path.parts),
                    reverse=True,
                ),
                check_only=check_only,
                planner=planner,
            )
        u.Infra.info(
            f"Lazy-init summary: {ok} generated, {errors} errors"
            f" ({total} dirs scanned)",
        )
        return errors

    def _generate_all_inits(
        self,
        pkg_dirs: Sequence[Path],
        *,
        check_only: bool,
        planner: FlextInfraCodegenLazyInitPlanner,
    ) -> tuple[int, int, int, MutableMapping[str, t.Infra.LazyImportMap]]:
        total = ok = errors = 0
        dir_exports: MutableMapping[str, t.Infra.LazyImportMap] = {}
        for pkg_dir in pkg_dirs:
            total += 1
            result, exports = self._process_directory(
                pkg_dir,
                check_only=check_only,
                dir_exports=dir_exports,
                planner=planner,
            )
            if exports:
                dir_exports[str(pkg_dir.resolve())] = exports
            if result is None:
                continue
            if result < 0:
                errors += 1
            else:
                ok += 1
        return total, ok, errors, dir_exports

    def _process_directory(
        self,
        pkg_dir: Path,
        *,
        check_only: bool,
        dir_exports: Mapping[str, t.Infra.LazyImportMap],
        planner: FlextInfraCodegenLazyInitPlanner,
    ) -> t.Infra.LazyInitProcessResult:
        try:
            plan = planner.build_plan(
                pkg_dir,
                dir_exports=dir_exports,
            )
            if plan.action == "skip":
                return (None, dict(plan.lazy_map))
            if check_only:
                return (0, dict(plan.lazy_map))
            if plan.action == "remove":
                return self._remove_init(plan)
            return self._write_init(
                plan.context.init_path,
                plan.exports,
                plan.lazy_map,
                plan.inline_constants,
                plan.context.current_pkg,
                wildcard_runtime_imports=plan.wildcard_runtime_modules,
                child_packages_for_lazy=plan.child_packages_for_lazy,
                child_packages_for_tc=plan.child_packages_for_tc,
            )
        except ValueError as exc:
            u.Infra.error(
                f"export collision in {pkg_dir}: {exc}; "
                "correct the source exports before regenerating __init__.py",
            )
            failed_lazy_map: t.Infra.MutableLazyImportMap = {}
            return (-1, failed_lazy_map)

    def _remove_init(
        self,
        plan: m.Infra.LazyInitPlan,
    ) -> t.Infra.LazyInitWriteResult:
        init_path = plan.context.init_path
        if not init_path.is_file():
            return (0, dict(plan.lazy_map))
        try:
            init_path.unlink()
        except OSError as exc:
            u.Infra.error(f"removing generated init {init_path}: {exc}")
            return (-1, dict(plan.lazy_map))
        self._modified_files.add(str(init_path))
        rel_path = (
            init_path.relative_to(self.workspace_root)
            if self.workspace_root in init_path.parents
            else init_path
        )
        u.Infra.info(f"  CLEAN: {rel_path} — removed generated init")
        return (0, dict(plan.lazy_map))

    def _write_init(
        self,
        init_path: Path,
        exports: t.StrSequence,
        lazy_map: t.Infra.LazyImportMap,
        inline_constants: t.StrMapping,
        current_pkg: str,
        eager_imports: t.Infra.LazyImportMap | None = None,
        wildcard_runtime_imports: t.StrSequence | None = None,
        child_packages_for_lazy: t.StrSequence | None = None,
        child_packages_for_tc: t.StrSequence | None = None,
    ) -> t.Infra.LazyInitWriteResult:
        try:
            generated = FlextInfraCodegenGeneration.generate_file(
                exports,
                lazy_map,
                inline_constants,
                current_pkg,
                eager_imports,
                wildcard_runtime_imports,
                child_packages_for_lazy=child_packages_for_lazy or [],
                child_packages_for_tc=child_packages_for_tc or [],
            )
            previous = (
                init_path.read_text(encoding=c.Infra.ENCODING_DEFAULT)
                if init_path.exists()
                else None
            )
            if previous != generated:
                write_result = u.Cli.atomic_write_text_file(init_path, generated)
                if write_result.failure:
                    u.Infra.error(f"writing {init_path}: {write_result.error}")
                    return (-1, dict(lazy_map))
                self._modified_files.add(str(init_path))
                u.Infra.run_ruff_fix(init_path, quiet=True)
        except (OSError, ValueError) as exc:
            u.Infra.error(f"generating {init_path}: {exc}")
            return (-1, dict(lazy_map))
        rel_path = (
            init_path.relative_to(self.workspace_root)
            if self.workspace_root in init_path.parents
            else init_path
        )
        u.Infra.info(f"  OK: {rel_path} — {len(exports)} exports")
        return (0, dict(lazy_map))


__all__ = ["FlextInfraCodegenLazyInit"]
