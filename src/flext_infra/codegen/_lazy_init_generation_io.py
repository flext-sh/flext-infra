"""Canonical IO for generated initializer artifact sets."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration
from flext_infra.constants import c
from flext_infra.utilities import u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_core.protocols import p as core_p

    from flext_infra.models import m
    from flext_infra.typings import t


# mro-i6nq.10: IO writes the manifest before its consuming root initializer.
class FlextInfraCodegenLazyInitGenerationIOMixin:
    """Compare, write, and remove generated package artifact sets."""

    if TYPE_CHECKING:
        workspace_root: Path
        _modified_files: t.Infra.StrSet

        def _cleanup_generated_support_files(
            self,
            plan: m.Infra.LazyInitPlan,
            *,
            check_only: bool = False,
        ) -> int: ...

        @staticmethod
        def _read_generated_file(path: Path) -> str | None: ...

    @staticmethod
    def _read_previous_init(plan: m.Infra.LazyInitPlan) -> str | None:
        """Read existing initializer content when present."""
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

    def _write_generated_file(
        self,
        path: Path,
        generated: str,
        previous: str | None,
    ) -> None:
        """Atomically write one changed canonical generated Python file."""
        if previous == generated:
            return
        write_result = u.Cli.atomic_write_text_file(path, generated)
        if write_result.failure:
            message = f"writing {path}: {write_result.error}"
            raise OSError(message)
        self._modified_files.add(str(path))

    @staticmethod
    def _normalize_generated_file(path: Path, generated: str) -> str:
        """Normalize generated Python before both comparison and writing."""
        # mro-i6nq.10: The artifact filename is Ruff's sole config-discovery key.
        normalized: core_p.Result[str] = u.Infra.normalize_python_source(
            generated,
            filename=path,
        )
        if normalized.failure:
            message = f"normalizing generated source {path}: {normalized.error}"
            raise OSError(message)
        return normalized.value

    def _sync_unit_manifest(
        self,
        plan: m.Infra.LazyInitPlan,
        generated: str | None,
        *,
        check_only: bool,
    ) -> None:
        """Create, compare, or remove the codegen-owned root manifest."""
        unit_path = plan.context.pkg_dir / c.Infra.UNIT_PY
        previous = self._read_generated_file(unit_path)
        if generated is None:
            if previous is None or not previous.startswith(c.Infra.AUTOGEN_HEADER):
                return
            self._modified_files.add(str(unit_path))
            if not check_only:
                unit_path.unlink()
            return
        if previous == generated:
            return
        if check_only:
            self._modified_files.add(str(unit_path))
            return
        self._write_generated_file(unit_path, generated, previous)

    def _check_remove_init(
        self,
        plan: m.Infra.LazyInitPlan,
    ) -> t.Infra.LazyInitWriteResult:
        """Record generated artifact removals without writing."""
        init_path = plan.context.init_path
        if init_path.is_file():
            self._modified_files.add(str(init_path))
        self._sync_unit_manifest(plan, None, check_only=True)
        return (0, dict(plan.lazy_map))

    def _remove_init(
        self,
        plan: m.Infra.LazyInitPlan,
    ) -> t.Infra.LazyInitWriteResult:
        """Remove the initializer before its generated manifest."""
        init_path = plan.context.init_path
        try:
            if init_path.is_file():
                init_path.unlink()
                self._modified_files.add(str(init_path))
            self._sync_unit_manifest(plan, None, check_only=False)
        except OSError as exc:
            u.Cli.error(f"removing generated init {init_path}: {exc}")
            return (-1, dict(plan.lazy_map))
        return (0, dict(plan.lazy_map))

    def _write_init(
        self,
        plan: m.Infra.LazyInitPlan,
    ) -> t.Infra.LazyInitWriteResult:
        """Write the manifest first and its consuming initializer second."""
        init_path = plan.context.init_path
        unit_path = plan.context.pkg_dir / c.Infra.UNIT_PY
        try:
            generated, generated_unit = (
                self._normalize_generated_file(
                    init_path,
                    FlextInfraCodegenGeneration.render_init(plan),
                ),
                self._normalize_generated_file(
                    unit_path,
                    FlextInfraCodegenGeneration.render_unit_manifest(plan),
                ),
            )
            previous = self._read_previous_init(plan)
            cleanup_exit = self._cleanup_generated_support_files(plan)
            self._sync_unit_manifest(plan, generated_unit, check_only=False)
            self._write_generated_file(init_path, generated, previous)
        except c.EXC_OS_VALUE as exc:
            u.Cli.error(f"generating {init_path}: {exc}")
            return (-1, dict(plan.lazy_map))
        if cleanup_exit < 0:
            return (-1, dict(plan.lazy_map))
        return (0, dict(plan.lazy_map))

    def _check_write_init(
        self,
        plan: m.Infra.LazyInitPlan,
    ) -> t.Infra.LazyInitWriteResult:
        """Compare both generated artifacts without mutating them."""
        init_path = plan.context.init_path
        unit_path = plan.context.pkg_dir / c.Infra.UNIT_PY
        try:
            generated = self._normalize_generated_file(
                init_path,
                FlextInfraCodegenGeneration.render_init(plan),
            )
            generated_unit = self._normalize_generated_file(
                unit_path,
                FlextInfraCodegenGeneration.render_unit_manifest(plan),
            )
            previous = self._read_previous_init(plan)
            cleanup_exit = self._cleanup_generated_support_files(
                plan,
                check_only=True,
            )
            self._sync_unit_manifest(plan, generated_unit, check_only=True)
        except c.EXC_OS_VALUE as exc:
            u.Cli.error(f"checking generated init {init_path}: {exc}")
            return (-1, dict(plan.lazy_map))
        if cleanup_exit < 0:
            return (-1, dict(plan.lazy_map))
        if previous != generated:
            self._modified_files.add(str(init_path))
        return (0, dict(plan.lazy_map))


__all__: list[str] = ["FlextInfraCodegenLazyInitGenerationIOMixin"]
