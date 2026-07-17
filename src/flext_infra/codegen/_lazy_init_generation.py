"""Lazy-init per-directory generation service — extracted concern.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, p, t, u
from flext_infra.codegen._lazy_init_generation_io import (
    FlextInfraCodegenLazyInitGenerationIOMixin,
)
from flext_infra.codegen._lazy_init_generation_registry import (
    FlextInfraCodegenLazyInitGenerationRegistryMixin,
)

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from pathlib import Path

    from flext_infra.codegen.lazy_init_planner import FlextInfraCodegenLazyInitPlanner


# mro-i6nq.10: Root manifests and initializers are synchronized as one artifact set.
class FlextInfraCodegenLazyInitGenerationMixin(
    FlextInfraCodegenLazyInitGenerationIOMixin,
    FlextInfraCodegenLazyInitGenerationRegistryMixin,
):
    """Generate/remove ``__init__.py`` per package directory."""

    if TYPE_CHECKING:
        workspace_root: Path
        _modified_files: t.Infra.StrSet

    def _generate_all_inits(
        self,
        pkg_dirs: t.SequenceOf[Path],
        *,
        check_only: bool,
        planner: FlextInfraCodegenLazyInitPlanner,
        target_package_dir: Path | None = None,
        target_includes_descendants: bool = False,
    ) -> tuple[int, int, int, MutableMapping[str, t.LazyAliasMap]]:
        total = ok = errors = 0
        dir_exports: MutableMapping[str, t.LazyAliasMap] = {}
        progress_interval = max(1, len(pkg_dirs) // 20) if pkg_dirs else 1
        for idx, pkg_dir in enumerate(pkg_dirs, start=1):
            total += 1
            if idx == 1 or idx == len(pkg_dirs) or idx % progress_interval == 0:
                rel_path = (
                    pkg_dir.relative_to(self.workspace_root)
                    if self.workspace_root in pkg_dir.parents
                    else pkg_dir
                )
                u.Cli.info(f"lazy-init: progress {idx}/{len(pkg_dirs)} — {rel_path}")
            result, exports = self._process_directory(
                pkg_dir,
                check_only=check_only,
                dir_exports=dir_exports,
                planner=planner,
                process=(
                    target_package_dir is None
                    or pkg_dir.resolve() == target_package_dir.resolve()
                    or (
                        target_includes_descendants
                        and target_package_dir.resolve() in pkg_dir.resolve().parents
                    )
                ),
            )
            if exports:
                dir_exports[str(pkg_dir.resolve())] = exports
            if result is None:
                continue
            if result < 0:
                errors += 1
            else:
                ok += 1
            if (
                target_package_dir is not None
                and pkg_dir.resolve() == target_package_dir.resolve()
            ):
                break
        return total, ok, errors, dir_exports

    def _process_directory(
        self,
        pkg_dir: Path,
        *,
        check_only: bool,
        dir_exports: t.MappingKV[str, t.LazyAliasMap],
        planner: FlextInfraCodegenLazyInitPlanner,
        process: bool = True,
    ) -> t.Infra.LazyInitProcessResult:
        """Process directory."""
        result: t.Infra.LazyInitProcessResult
        failed_lazy_map: t.MutableLazyAliasMap
        try:
            plan = planner.build_plan(pkg_dir, dir_exports=dir_exports)
        except ValueError as exc:
            u.Cli.error(
                f"export collision in {pkg_dir}: {exc}; "
                "correct the source exports before regenerating __init__.py"
            )
            failed_lazy_map = {}
            result = (-1, failed_lazy_map)
        except c.EXC_OS_VALUE as exc:
            u.Cli.error(f"generating {pkg_dir}: {exc}")
            failed_lazy_map = {}
            result = (-1, failed_lazy_map)
        else:
            result = (
                self._process_plan(plan, check_only=check_only)
                if process
                else (None, dict(plan.lazy_map))
            )
        return result

    def _process_plan(
        self, plan: p.Infra.LazyInitPlan, *, check_only: bool
    ) -> t.Infra.LazyInitProcessResult:
        """Process a resolved lazy-init plan."""
        if plan.action == c.Infra.LazyInitAction.SKIP:
            return (None, dict(plan.lazy_map))
        if plan.action == c.Infra.LazyInitAction.REMOVE:
            return (
                self._check_remove_init(plan) if check_only else self._remove_init(plan)
            )
        if check_only:
            return self._check_write_init(plan)
        return self._write_init(plan)


__all__: list[str] = ["FlextInfraCodegenLazyInitGenerationMixin"]
