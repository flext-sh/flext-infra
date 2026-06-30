"""Lazy-init generated registry file writes."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, t, u
from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration


class FlextInfraCodegenLazyInitEngineRegistryMixin:
    """Write split lazy registries for generated test wrappers."""

    if TYPE_CHECKING:
        _modified_files: t.Infra.StrSet

    def _write_generated_registry(
        self,
        plan: m.Infra.LazyInitPlan,
        generated_init: str,
    ) -> int:
        """Write split registry files when the generated init uses them."""
        registry = plan.registry_wrapper
        if registry is None or not registry.generated:
            return 0
        import_line = f"from {registry.module} import {registry.name}"
        if import_line not in generated_init:
            return 0
        files = FlextInfraCodegenGeneration.generate_registry_files(
            plan.context.current_pkg,
            registry.name,
            plan.lazy_map,
            plan.child_packages_for_lazy,
            plan.excluded_lazy_names,
        )
        if not files:
            return 0
        try:
            self._remove_stale_registry_parts(plan, frozenset(files))
            for relative_name, content in files.items():
                self._write_changed_generated_file(
                    plan.context.pkg_dir / relative_name,
                    content,
                )
        except c.EXC_OS_VALUE as exc:
            u.Cli.error(f"generating registry for {plan.context.pkg_dir}: {exc}")
            return -1
        return 0

    def _remove_stale_registry_parts(
        self,
        plan: m.Infra.LazyInitPlan,
        expected_names: frozenset[str],
    ) -> None:
        """Remove generated registry part files no longer referenced."""
        for path in sorted(plan.context.pkg_dir.glob("_exports_lazy_part_*.py")):
            if path.name in expected_names:
                continue
            previous = self._read_generated_file(path)
            if previous is None or not previous.startswith(c.Infra.AUTOGEN_HEADER):
                continue
            path.unlink()
            self._modified_files.add(str(path))

    def _write_changed_generated_file(self, path: Path, generated: str) -> None:
        """Write generated support files when content changed."""
        previous = self._read_generated_file(path)
        if previous == generated:
            return
        write_result = u.Cli.atomic_write_text_file(path, generated)
        if write_result.failure:
            message = f"writing {path}: {write_result.error}"
            raise OSError(message)
        self._modified_files.add(str(path))
        _ = u.Infra.run_ruff_fix(path, quiet=True)

    @staticmethod
    def _read_generated_file(path: Path) -> str | None:
        """Read an optional generated support file."""
        if not path.exists():
            return None
        read = u.Cli.files_read_text(path)
        if read.failure:
            message = f"reading {path}: {read.error}"
            raise OSError(message)
        content = read.value
        if isinstance(content, str):
            return content
        message = f"reading {path}: expected text content"
        raise TypeError(message)


__all__: list[str] = ["FlextInfraCodegenLazyInitEngineRegistryMixin"]
