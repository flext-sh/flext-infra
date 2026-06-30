"""Lazy-init per-directory generation engine — extracted concern."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, t, u
from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration
from flext_infra.codegen.lazy_init_planner import FlextInfraCodegenLazyInitPlanner


class FlextInfraCodegenLazyInitEngineMixin:
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
        dir_exports: t.MappingKV[str, t.LazyAliasMap],
        planner: FlextInfraCodegenLazyInitPlanner,
    ) -> t.Infra.LazyInitProcessResult:
        """Process directory."""
        result: t.Infra.LazyInitProcessResult
        failed_lazy_map: t.MutableLazyAliasMap
        try:
            plan = planner.build_plan(
                pkg_dir,
                dir_exports=dir_exports,
            )
        except ValueError as exc:
            u.Cli.error(
                f"export collision in {pkg_dir}: {exc}; "
                "correct the source exports before regenerating __init__.py",
            )
            failed_lazy_map = {}
            result = (-1, failed_lazy_map)
        except c.EXC_OS_VALUE as exc:
            u.Cli.error(f"generating {pkg_dir}: {exc}")
            failed_lazy_map = {}
            result = (-1, failed_lazy_map)
        else:
            result = self._process_plan(plan, check_only=check_only)
        return result

    def _process_plan(
        self,
        plan: m.Infra.LazyInitPlan,
        *,
        check_only: bool,
    ) -> t.Infra.LazyInitProcessResult:
        """Process a resolved lazy-init plan."""
        if plan.action == c.Infra.LazyInitAction.SKIP:
            return (None, dict(plan.lazy_map))
        if check_only:
            return (0, dict(plan.lazy_map))
        if plan.action == c.Infra.LazyInitAction.REMOVE:
            return self._remove_init(plan)
        return self._write_init(plan)

    def _remove_init(
        self,
        plan: m.Infra.LazyInitPlan,
    ) -> t.Infra.LazyInitWriteResult:
        """Remove init."""
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
        plan: m.Infra.LazyInitPlan,
    ) -> t.Infra.LazyInitWriteResult:
        """Write init."""
        init_path = plan.context.init_path
        try:
            generated = self._render_init(plan)
            previous = self._read_previous_init(plan)
            write_exit = self._write_changed_init(plan, generated, previous)
        except c.EXC_OS_VALUE as exc:
            u.Cli.error(f"generating {init_path}: {exc}")
            return (-1, dict(plan.lazy_map))
        if write_exit < 0:
            return (-1, dict(plan.lazy_map))
        rel_path = (
            init_path.relative_to(self.workspace_root)
            if self.workspace_root in init_path.parents
            else init_path
        )
        u.Cli.info(f"  OK: {rel_path} — {len(plan.exports)} exports")
        return (0, dict(plan.lazy_map))

    @staticmethod
    def _render_init(plan: m.Infra.LazyInitPlan) -> str:
        """Render generated __init__.py content for a lazy-init plan."""
        return FlextInfraCodegenGeneration.generate_file(
            plan.exports,
            plan.lazy_map,
            plan.inline_constants,
            plan.context.current_pkg,
            eager_imports=plan.eager_dunders,
            type_checking_imports=plan.type_checking_map,
            wildcard_runtime_modules=plan.wildcard_runtime_modules,
            child_packages_for_lazy=plan.child_packages_for_lazy,
            excluded_lazy_names=plan.excluded_lazy_names,
            registry_wrapper=plan.registry_wrapper,
        )

    @staticmethod
    def _read_previous_init(plan: m.Infra.LazyInitPlan) -> str | None:
        """Read existing __init__.py content when it exists."""
        init_path = plan.context.init_path
        if not init_path.exists():
            return None
        read = u.Cli.files_read_text(init_path)
        if read.failure:
            message = f"reading {init_path}: {read.error}"
            raise OSError(message)
        content = read.value
        if isinstance(content, str):
            return content
        message = f"reading {init_path}: expected text content"
        raise TypeError(message)

    def _write_changed_init(
        self,
        plan: m.Infra.LazyInitPlan,
        generated: str,
        previous: str | None,
    ) -> int:
        """Write generated __init__.py content when it changed."""
        if previous == generated:
            return 0
        init_path = plan.context.init_path
        write_result = u.Cli.atomic_write_text_file(init_path, generated)
        if write_result.failure:
            message = f"writing {init_path}: {write_result.error}"
            raise OSError(message)
        self._modified_files.add(str(init_path))
        _ = u.Infra.run_ruff_fix(init_path, quiet=True)
        return 0


__all__: list[str] = ["FlextInfraCodegenLazyInitEngineMixin"]
