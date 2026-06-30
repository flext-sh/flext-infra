"""Lazy-init generated initializer IO helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import m, t, u


class FlextInfraCodegenLazyInitEngineIOMixin:
    """Read and write generated ``__init__.py`` files."""

    if TYPE_CHECKING:
        _modified_files: t.Infra.StrSet

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


__all__: list[str] = ["FlextInfraCodegenLazyInitEngineIOMixin"]
