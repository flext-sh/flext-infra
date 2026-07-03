"""Lazy-init generated registry file writes."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraCodegenLazyInitGenerationRegistryMixin:
    """Write split lazy registries for generated test wrappers."""

    if TYPE_CHECKING:
        _modified_files: t.Infra.StrSet

    def _write_generated_registry(
        self,
        plan: m.Infra.LazyInitPlan,
        generated_init: str,
        *,
        check_only: bool = False,
    ) -> int:
        """Write split registries and static stubs for generated init files."""
        if plan.context.current_pkg == "flext_core":
            try:
                self._write_generated_typing_stub(plan, check_only=check_only)
            except c.EXC_OS_VALUE as exc:
                u.Cli.error(f"generating typing stub for {plan.context.pkg_dir}: {exc}")
                return -1
            return 0
        registry = plan.registry_wrapper
        if registry is None:
            try:
                self._write_generated_typing_stub(plan, check_only=check_only)
            except c.EXC_OS_VALUE as exc:
                u.Cli.error(f"generating typing stub for {plan.context.pkg_dir}: {exc}")
                return -1
            return 0
        import_line = f"from {registry.module} import {registry.name}"
        import_block = f"from {registry.module} import ("
        imports_registry = import_line in generated_init or (
            import_block in generated_init and f"    {registry.name}," in generated_init
        )
        if not imports_registry:
            self._remove_generated_registry_wrapper(
                plan,
                registry,
                check_only=check_only,
            )
            self._remove_generated_typing_stub(plan, check_only=check_only)
            return 0
        if not registry.generated:
            try:
                self._write_generated_typing_stub(plan, check_only=check_only)
            except c.EXC_OS_VALUE as exc:
                u.Cli.error(
                    f"generating registry stub for {plan.context.pkg_dir}: {exc}"
                )
                return -1
            return 0
        registry_dir = self._registry_dir_for_module(
            plan.context.pkg_dir,
            registry.module,
        )
        registry_rel_module = registry.module.removeprefix(
            f"{plan.context.current_pkg}."
        )
        registry_filename = f"{registry_rel_module.replace('.', '/')}.py"
        files = FlextInfraCodegenGeneration.generate_registry_files(
            plan.context.current_pkg,
            registry.name,
            plan.lazy_map,
            plan.child_packages_for_lazy,
            plan.excluded_lazy_names,
            registry_filename=registry_filename,
        )
        if not files:
            self._remove_generated_typing_stub(plan, check_only=check_only)
            return 0
        try:
            self._ensure_constants_init(registry_dir, check_only=check_only)
            self._remove_stale_registry_parts(
                plan,
                frozenset(files),
                check_only=check_only,
            )
            for relative_name, content in files.items():
                self._write_changed_generated_file(
                    plan.context.pkg_dir / relative_name,
                    content,
                    check_only=check_only,
                )
            self._write_generated_typing_stub(plan, check_only=check_only)
        except c.EXC_OS_VALUE as exc:
            u.Cli.error(f"generating registry for {plan.context.pkg_dir}: {exc}")
            return -1
        return 0

    def _write_generated_typing_stub(
        self,
        plan: m.Infra.LazyInitPlan,
        *,
        check_only: bool = False,
    ) -> None:
        """Write the static typing stub for generated lazy exports."""
        if not self._should_emit_typing_stub(plan):
            self._remove_generated_typing_stub(plan, check_only=check_only)
            return
        stub = (
            FlextInfraCodegenGeneration.generate_flext_core_root_typing_stub()
            if plan.context.current_pkg == "flext_core"
            else FlextInfraCodegenGeneration.generate_typing_stub(
                plan.exports,
                {**plan.type_checking_map, **plan.eager_dunders},
                plan.inline_constants,
                include_all=True,
            )
        )
        if stub:
            self._write_changed_generated_file(
                plan.context.pkg_dir / c.Infra.INIT_PYI,
                stub,
                check_only=check_only,
            )
            return
        self._remove_generated_typing_stub(plan, check_only=check_only)

    @staticmethod
    def _should_emit_typing_stub(plan: m.Infra.LazyInitPlan) -> bool:
        """Return whether a package owns a public static typing stub."""
        segments = tuple(
            segment for segment in plan.context.current_pkg.split(".") if segment
        )
        if not segments:
            return False
        if any(segment in c.Infra.NON_PUBLIC_LAZY_ROOTS for segment in segments):
            return False
        return not any(
            segment.startswith("_") and not segment.startswith("__")
            for segment in segments[1:]
        )

    def _remove_generated_typing_stub(
        self,
        plan: m.Infra.LazyInitPlan,
        *,
        check_only: bool = False,
    ) -> None:
        """Remove stale codegen-owned typing stubs when no static contract exists."""
        stub_path = plan.context.pkg_dir / c.Infra.INIT_PYI
        previous = self._read_generated_file(stub_path)
        if previous is None or not previous.startswith(c.Infra.AUTOGEN_HEADER):
            return
        if check_only:
            self._modified_files.add(str(stub_path))
            return
        stub_path.unlink()
        self._modified_files.add(str(stub_path))

    def _remove_stale_registry_parts(
        self,
        plan: m.Infra.LazyInitPlan,
        expected_names: frozenset[str],
        *,
        check_only: bool = False,
    ) -> None:
        """Remove generated registry part files no longer referenced."""
        registry_dir = self._registry_dir_for_module(
            plan.context.pkg_dir,
            plan.registry_wrapper.module if plan.registry_wrapper else "",
        )
        for base_dir in {plan.context.pkg_dir, registry_dir}:
            for path in sorted(base_dir.glob("_exports_lazy_part_*.py")):
                relative = str(path.relative_to(plan.context.pkg_dir))
                if relative in expected_names:
                    continue
                previous = self._read_generated_file(path)
                if previous is None or not previous.startswith(c.Infra.AUTOGEN_HEADER):
                    continue
                if check_only:
                    self._modified_files.add(str(path))
                    continue
                path.unlink()
                self._modified_files.add(str(path))

    def _remove_generated_registry_wrapper(
        self,
        plan: m.Infra.LazyInitPlan,
        registry: m.Infra.LazyInitRegistryWrapper,
        *,
        check_only: bool = False,
    ) -> None:
        """Remove stale generated registry files no longer imported by ``__init__``."""
        registry_relative = registry.module.removeprefix(f"{plan.context.current_pkg}.")
        registry_path = (
            plan.context.pkg_dir / f"{registry_relative.replace('.', '/')}.py"
        )
        previous = self._read_generated_file(registry_path)
        if previous is not None and previous.startswith(c.Infra.AUTOGEN_HEADER):
            if check_only:
                self._modified_files.add(str(registry_path))
            else:
                registry_path.unlink()
                self._modified_files.add(str(registry_path))
        self._remove_stale_registry_parts(plan, frozenset(), check_only=check_only)

    def _ensure_constants_init(
        self,
        registry_dir: Path,
        *,
        check_only: bool = False,
    ) -> None:
        """Create or report a minimal ``_constants/__init__.py`` when missing."""
        if registry_dir.name != c.Infra.ROOT_EXPORTS_DIR:
            return
        init_path = registry_dir / c.Infra.INIT_PY
        if init_path.is_file():
            return
        content = self._constants_init_content()
        if check_only:
            self._modified_files.add(str(init_path))
            return
        write_result = u.Cli.atomic_write_text_file(init_path, content)
        if write_result.failure:
            message = f"writing {init_path}: {write_result.error}"
            raise OSError(message)
        self._modified_files.add(str(init_path))

    @staticmethod
    def _constants_init_content() -> str:
        """Return canonical generated constants package init content."""
        return (
            f"{c.Infra.AUTOGEN_HEADER}\n"
            f'"""Constants package."""\n\n'
            f"from __future__ import annotations\n"
        )

    @staticmethod
    def _registry_dir_for_module(pkg_dir: Path, module: str) -> Path:
        """Return the directory where a registry module's files must live."""
        suffix = f".{c.Infra.ROOT_EXPORTS_DIR}.{c.Infra.ROOT_EXPORTS_FILENAME.removesuffix('.py')}"
        if module.endswith(suffix):
            root_exports_dir: str = c.Infra.ROOT_EXPORTS_DIR
            return pkg_dir / root_exports_dir
        return pkg_dir

    def _write_changed_generated_file(
        self,
        path: Path,
        generated: str,
        *,
        check_only: bool = False,
    ) -> None:
        """Write generated support files when content changed."""
        previous = self._read_generated_file(path)
        if previous == generated:
            return
        if check_only:
            self._modified_files.add(str(path))
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


__all__: list[str] = ["FlextInfraCodegenLazyInitGenerationRegistryMixin"]
