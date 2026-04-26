"""Lazy-init ``__init__.py`` generator (PEP 562).

Auto-discovers exports from sibling ``.py`` files and generates clean
lazy-loading ``__init__.py`` files using ``flext_core``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import (
    Mapping,
    MutableMapping,
    Sequence,
)
from pathlib import Path
from time import perf_counter
from typing import override

from flext_infra import (
    FlextInfraCodegenGeneration,
    FlextInfraCodegenLazyInitPlanner,
    FlextInfraRopeWorkspace,
    c,
    m,
    p,
    r,
    s,
    t,
    u,
)


class FlextInfraCodegenLazyInit(s[bool]):
    """Generates ``__init__.py`` with PEP 562 lazy imports.

    Scans sibling ``.py`` files in each package directory, discovers their
    exports, and generates clean lazy-loading ``__init__.py`` files.
    Processes bottom-up so child packages are generated before parents.
    """

    _modified_files: t.Infra.StrSet = u.PrivateAttr()
    _duplicate_class_names: int = u.PrivateAttr(default_factory=lambda: 0)

    @override
    def model_post_init(self, __context: t.ScalarMapping | None, /) -> None:
        """Create private lazy-init state after model validation."""
        super().model_post_init(__context)
        self._modified_files = set()
        self._duplicate_class_names = 0

    @property
    def modified_files(self) -> t.StrSequence:
        """Return generated __init__.py files that changed on disk."""
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
        u.Cli.info(
            f"Lazy-init summary: {ok} generated, {errors} errors"
            f" ({total} dirs scanned, {perf_counter() - started_at:.2f}s)",
        )
        return errors

    @staticmethod
    def _detect_duplicate_class_names(
        rope: FlextInfraRopeWorkspace,
    ) -> Mapping[str, tuple[str, ...]]:
        """Return class-name collisions.

        Scope rules:
        - ``src/`` modules: duplicates forbidden across the entire workspace.
        - ``tests/``/``scripts/``/``examples/``/``docs/`` modules: duplicates
          forbidden only within the same owning project (they do not escape).
        """
        scoped_modules: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
        for entry in rope.workspace_index.modules_by_path.values():
            if entry.is_package_init or not entry.module_name:
                continue
            first_segment = entry.module_name.partition(".")[0]
            is_private_scope = first_segment in c.Infra.ROOT_WRAPPER_SEGMENTS
            scope_key = (
                str(entry.project_root)
                if is_private_scope and entry.project_root is not None
                else ""
            )
            state = rope.semantic(entry.file_path)
            for class_info in state.class_infos:
                name = class_info.name
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

    def _generate_all_inits(
        self,
        pkg_dirs: Sequence[Path],
        *,
        check_only: bool,
        planner: FlextInfraCodegenLazyInitPlanner,
    ) -> tuple[int, int, int, MutableMapping[str, t.Infra.LazyImportMap]]:
        total = ok = errors = 0
        dir_exports: MutableMapping[str, t.Infra.LazyImportMap] = {}
        progress_interval = max(1, len(pkg_dirs) // 20) if pkg_dirs else 1
        for idx, pkg_dir in enumerate(pkg_dirs, start=1):
            total += 1
            if idx == 1 or idx == len(pkg_dirs) or idx % progress_interval == 0:
                rel_path = (
                    pkg_dir.relative_to(self.workspace_root)
                    if self.workspace_root in pkg_dir.parents
                    else pkg_dir
                )
                u.Cli.info(
                    f"lazy-init: progress {idx}/{len(pkg_dirs)} — {rel_path}",
                )
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
            u.Cli.error(
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
            u.Cli.error(f"removing generated init {init_path}: {exc}")
            return (-1, dict(plan.lazy_map))
        self._modified_files.add(str(init_path))
        rel_path = (
            init_path.relative_to(self.workspace_root)
            if self.workspace_root in init_path.parents
            else init_path
        )
        u.Cli.info(f"  CLEAN: {rel_path} — removed generated init")
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
                init_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
                if init_path.exists()
                else None
            )
            if previous != generated:
                write_result = u.Cli.atomic_write_text_file(init_path, generated)
                if write_result.failure:
                    u.Cli.error(f"writing {init_path}: {write_result.error}")
                    return (-1, dict(lazy_map))
                self._modified_files.add(str(init_path))
                u.Infra.run_ruff_fix(init_path, quiet=True)
        except (OSError, ValueError) as exc:
            u.Cli.error(f"generating {init_path}: {exc}")
            return (-1, dict(lazy_map))
        rel_path = (
            init_path.relative_to(self.workspace_root)
            if self.workspace_root in init_path.parents
            else init_path
        )
        u.Cli.info(f"  OK: {rel_path} — {len(exports)} exports")
        return (0, dict(lazy_map))


__all__: list[str] = ["FlextInfraCodegenLazyInit"]
