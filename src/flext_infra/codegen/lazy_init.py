"""Lazy-init ``__init__.py`` publication planner (PEP 562).

Auto-discovers exports from sibling ``.py`` files and describes clean
lazy-loading ``__init__.py`` artifacts using ``flext_core``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING, override

from flext_core import r
from flext_infra import c, config, m, u
from flext_infra._utilities._sort_keys import path_depth
from flext_infra.base import s
from flext_infra.codegen._lazy_init_generation import (
    FlextInfraCodegenLazyInitGenerationMixin,
)
from flext_infra.codegen.lazy_init_planner import FlextInfraCodegenLazyInitPlanner
from flext_infra.workspace.rope import FlextInfraRopeWorkspace

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraCodegenLazyInit(s[bool], FlextInfraCodegenLazyInitGenerationMixin):
    """Plan ``__init__.py`` artifacts with PEP 562 lazy imports.

    Scans sibling ``.py`` files in each package directory, discovers their
    exports, and returns immutable file plans for the generation transaction.
    Processes bottom-up so child packages are generated before parents.
    """

    _modified_files: t.Infra.StrSet = u.PrivateAttr(default_factory=set)
    _duplicate_class_names: int = u.PrivateAttr(default_factory=lambda: 0)

    @property
    def modified_files(self) -> t.StrSequence:
        """Initializer artifacts whose immutable plans require an effect."""
        return tuple(sorted(self._modified_files))

    @override
    def execute(self) -> p.Result[bool]:
        """Check lazy-init drift; publication belongs to conform's transaction."""
        planned = self.plan_files()
        if planned.failure:
            return r[bool].from_failure(planned)
        if not self.effective_dry_run:
            return r[bool].fail(
                "lazy-init publication is owned by codegen conform; "
                "the generation transaction must publish plan_files()"
            )
        changed = tuple(
            plan
            for plan in planned.value.files
            if u.Infra.codegen_file_requires_effect(plan)
        )
        if changed:
            drifted_files = ", ".join(str(plan.path) for plan in changed)
            return r[bool].fail(
                f"init drift detected in {len(changed)} "
                f"generated artifacts: {drifted_files}"
            )
        return r[bool].ok(True)

    def plan_files(self) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Return one complete immutable lazy-init analysis receipt."""
        self._modified_files.clear()
        self._duplicate_class_names = 0
        if not self.repository_root.is_dir():
            return r[m.Infra.CodegenPhaseAnalysis].fail(
                f"lazy-init repository is not a directory: {self.repository_root}"
            )
        started_at = perf_counter()
        u.Cli.info(
            f"lazy-init: planning read-only artifacts for {self.repository_root}"
        )
        planned = self._plan_in_workspace()
        if planned.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(planned)
        analysis = planned.value
        changed = tuple(
            plan
            for plan in analysis.files
            if u.Infra.codegen_file_requires_effect(plan)
        )
        self._modified_files.update(str(plan.path) for plan in changed)
        u.Cli.info(
            f"Lazy-init plan: {len(changed)} effects "
            f"({perf_counter() - started_at:.2f}s)"
        )
        return r[m.Infra.CodegenPhaseAnalysis].ok(analysis)

    def _plan_in_workspace(self) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Open Rope once and propagate every planner or filesystem failure."""
        try:
            with FlextInfraRopeWorkspace.open_workspace(
                self.repository_root, rope_repository_root=self.repository_root
            ) as rope:
                return self._plan_open_workspace(rope)
        except c.EXC_OS_VALUE as exc:
            return r[m.Infra.CodegenPhaseAnalysis].fail_op("lazy-init planning", exc)

    def _plan_open_workspace(
        self, rope: FlextInfraRopeWorkspace
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Build immutable plans from one stable Rope workspace snapshot."""
        workspace_index = rope.workspace_index
        resolved_workspace_root = self.repository_root.resolve()
        indexed_package_dirs = tuple(
            sorted(
                (
                    package_dir.resolve()
                    for package_dir in workspace_index.package_dirs
                    if package_dir.is_relative_to(resolved_workspace_root)
                    and not frozenset(
                        package_dir.relative_to(resolved_workspace_root).parts
                    )
                    & c.Infra.OBSOLETE_ROOT_SUPPORT_NAMES
                ),
                key=path_depth,
                reverse=True,
            )
        )
        target_package_dir: Path | None = None
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
                return r[m.Infra.CodegenPhaseAnalysis].fail(
                    f"lazy-init target module not found: {self.target_module}"
                )
            if sorted_target_dirs[1:]:
                return r[m.Infra.CodegenPhaseAnalysis].fail(
                    f"lazy-init target module is ambiguous: {self.target_module}"
                )
            target_package_dir = sorted_target_dirs[0]
            if target_package_dir not in indexed_package_dirs:
                return r[m.Infra.CodegenPhaseAnalysis].fail(
                    f"lazy-init target belongs to retired support: {self.target_module}"
                )
        package_dirs = self._package_dirs_for_target(
            indexed_package_dirs,
            target_package_dir=target_package_dir,
            workspace_root=resolved_workspace_root,
        )
        snapshots = self._snapshot_planner_inputs(workspace_index)
        if snapshots.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(snapshots)
        duplicates = self._detect_duplicate_class_names(rope, package_dirs=package_dirs)
        if duplicates:
            self._duplicate_class_names = len(duplicates)
            details = "; ".join(
                f"{name}: {', '.join(locations)}"
                for name, locations in sorted(duplicates.items())
            )
            return r[m.Infra.CodegenPhaseAnalysis].fail(
                "lazy-init duplicate class names must be renamed before planning: "
                f"{details}"
            )
        planner = FlextInfraCodegenLazyInitPlanner(
            rope_workspace=rope, lazy_init=config.Infra.tooling.lazy_init
        )
        u.Cli.info(f"lazy-init: planning {len(package_dirs)} package dirs")
        package_plans = self._plan_all_inits(
            package_dirs, planner=planner, target_package_dir=target_package_dir
        )
        if planner.collision_count:
            return r[m.Infra.CodegenPhaseAnalysis].fail(
                "lazy-init public export ownership is ambiguous: "
                f"{planner.collision_count} collision(s)"
            )
        file_plans = self._build_file_plans(
            package_plans, index=workspace_index, snapshots=snapshots.value
        )
        if file_plans.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(file_plans)
        stable = self._verify_snapshots(snapshots.value)
        if stable.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(stable)
        return r[m.Infra.CodegenPhaseAnalysis].ok(
            m.Infra.CodegenPhaseAnalysis(
                phase="lazy-init",
                files=file_plans.value,
                inputs=tuple(snapshots.value[path] for path in sorted(snapshots.value)),
            )
        )

    @staticmethod
    def _package_dirs_for_target(
        indexed_package_dirs: t.SequenceOf[Path],
        *,
        target_package_dir: Path | None,
        workspace_root: Path,
    ) -> tuple[Path, ...]:
        """Select the target's source/test scope and its production sibling."""
        if target_package_dir is None:
            return tuple(indexed_package_dirs)
        target_parts = target_package_dir.relative_to(workspace_root).parts
        boundary_names = frozenset({
            c.Infra.DEFAULT_SRC_DIR,
            *c.Infra.NON_PUBLIC_LAZY_ROOTS,
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
        return tuple(
            package_dir
            for package_dir in indexed_package_dirs
            if package_dir.relative_to(workspace_root).parts[: len(scope_prefix)]
            == scope_prefix
            or package_dir.relative_to(workspace_root).parts[: len(production_prefix)]
            == production_prefix
        )

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
