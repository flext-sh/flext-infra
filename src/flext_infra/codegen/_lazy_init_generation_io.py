"""Canonical IO for generated initializer artifact sets."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, u
from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, t


# mro-wkii.17.26 (codex): IO owns one initializer and removes obsolete sidecars.
class FlextInfraCodegenLazyInitGenerationIOMixin:
    """Compare, write, and remove generated package initializers."""

    if TYPE_CHECKING:
        workspace_root: Path
        _modified_files: t.Infra.StrSet

        def _cleanup_generated_support_files(
            self, plan: m.Infra.LazyInitPlan, *, check_only: bool = False
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
        self, path: Path, generated: str, previous: str | None
    ) -> None:
        """Atomically write one changed canonical generated Python file."""
        if previous == generated:
            return
        write_result = u.Cli.atomic_write_text_file(path, generated)
        if write_result.failure:
            message = f"writing {path}: {write_result.error}"
            raise OSError(message)
        self._modified_files.add(str(path))

    def _sync_typing_stub(
        self,
        plan: m.Infra.LazyInitPlan,
        generated: str | None,
        *,
        check_only: bool = False,
    ) -> None:
        """Synchronize the generated public-root stub or remove a stale one."""
        stub_path = plan.context.pkg_dir / c.Infra.INIT_PYI
        previous = self._read_generated_file(stub_path)
        generated_owned = previous is not None and previous.startswith(
            c.Infra.AUTOGEN_HEADER
        )
        if generated is None:
            if not generated_owned:
                return
            if check_only:
                self._modified_files.add(str(stub_path))
            else:
                stub_path.unlink()
                self._modified_files.add(str(stub_path))
            return
        if previous is not None and not generated_owned and previous != generated:
            message = f"refusing to overwrite hand-written typing stub: {stub_path}"
            raise OSError(message)
        if check_only:
            if previous != generated:
                self._modified_files.add(str(stub_path))
            return
        self._write_generated_file(stub_path, generated, previous)

    def _write_artifact_set(self, plan: m.Infra.LazyInitPlan) -> int:
        """Render and write one initializer with its matching typing stub."""
        generated = FlextInfraCodegenGeneration.render_init(plan)
        generated_stub = FlextInfraCodegenGeneration.render_typing_stub(plan)
        previous = self._read_previous_init(plan)
        cleanup_exit = self._cleanup_generated_support_files(plan)
        self._write_generated_file(plan.context.init_path, generated, previous)
        self._sync_typing_stub(plan, generated_stub)
        return cleanup_exit

    def _check_remove_init(
        self, plan: m.Infra.LazyInitPlan
    ) -> t.Infra.LazyInitWriteResult:
        """Record generated artifact removals without writing."""
        init_path = plan.context.init_path
        if init_path.is_file():
            self._modified_files.add(str(init_path))
        self._cleanup_generated_support_files(plan, check_only=True)
        self._sync_typing_stub(plan, None, check_only=True)
        return (0, dict(plan.lazy_map))

    def _remove_init(self, plan: m.Infra.LazyInitPlan) -> t.Infra.LazyInitWriteResult:
        """Remove the initializer and every obsolete generated sidecar."""
        init_path = plan.context.init_path
        try:
            if init_path.is_file():
                init_path.unlink()
                self._modified_files.add(str(init_path))
            cleanup_exit = self._cleanup_generated_support_files(plan)
            self._sync_typing_stub(plan, None)
        except OSError as exc:
            u.Cli.error(f"removing generated init {init_path}: {exc}")
            return (-1, dict(plan.lazy_map))
        if cleanup_exit < 0:
            return (-1, dict(plan.lazy_map))
        return (0, dict(plan.lazy_map))

    def _write_init(self, plan: m.Infra.LazyInitPlan) -> t.Infra.LazyInitWriteResult:
        """Write one initializer after removing obsolete generated sidecars."""
        init_path = plan.context.init_path
        try:
            # mro-j47u (codex): Jinja owns final Ruff shape; IO only compares/writes.
            cleanup_exit = self._write_artifact_set(plan)
        except c.EXC_OS_VALUE as exc:
            u.Cli.error(f"generating {init_path}: {exc}")
            return (-1, dict(plan.lazy_map))
        if cleanup_exit < 0:
            return (-1, dict(plan.lazy_map))
        return (0, dict(plan.lazy_map))

    def _check_write_init(
        self, plan: m.Infra.LazyInitPlan
    ) -> t.Infra.LazyInitWriteResult:
        """Compare the initializer and obsolete sidecars without mutating them."""
        init_path = plan.context.init_path
        try:
            generated = FlextInfraCodegenGeneration.render_init(plan)
            generated_stub = FlextInfraCodegenGeneration.render_typing_stub(plan)
            previous = self._read_previous_init(plan)
            cleanup_exit = self._cleanup_generated_support_files(plan, check_only=True)
            self._sync_typing_stub(plan, generated_stub, check_only=True)
        except c.EXC_OS_VALUE as exc:
            u.Cli.error(f"checking generated init {init_path}: {exc}")
            return (-1, dict(plan.lazy_map))
        if cleanup_exit < 0:
            return (-1, dict(plan.lazy_map))
        if previous != generated:
            self._modified_files.add(str(init_path))
        return (0, dict(plan.lazy_map))


__all__: list[str] = ["FlextInfraCodegenLazyInitGenerationIOMixin"]
