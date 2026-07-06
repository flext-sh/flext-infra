"""Lazy-init generated support-file cleanup."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.constants import c
from flext_infra.utilities import u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.models import m
    from flext_infra.typings import t


class FlextInfraCodegenLazyInitGenerationRegistryMixin:
    """Remove stale generated sidecars for package initializers."""

    if TYPE_CHECKING:
        _modified_files: t.Infra.StrSet

    def _cleanup_generated_support_files(
        self,
        plan: m.Infra.LazyInitPlan,
        *,
        check_only: bool = False,
    ) -> int:
        """Remove generated files superseded by inline ``__init__.py`` maps."""
        try:
            self._remove_generated_export_sidecars(plan, check_only=check_only)
            self._remove_generated_typing_stub(plan, check_only=check_only)
        except c.EXC_OS_VALUE as exc:
            u.Cli.error(
                f"cleaning generated sidecars for {plan.context.pkg_dir}: {exc}",
            )
            return -1
        return 0

    def _remove_generated_typing_stub(
        self,
        plan: m.Infra.LazyInitPlan,
        *,
        check_only: bool = False,
    ) -> None:
        """Remove stale codegen-owned ``__init__.pyi`` files."""
        stub_path = plan.context.pkg_dir / c.Infra.INIT_PYI
        previous = self._read_generated_file(stub_path)
        if previous is None or not previous.startswith(c.Infra.AUTOGEN_HEADER):
            return
        if check_only:
            self._modified_files.add(str(stub_path))
            return
        stub_path.unlink()
        self._modified_files.add(str(stub_path))

    def _remove_generated_export_sidecars(
        self,
        plan: m.Infra.LazyInitPlan,
        *,
        check_only: bool = False,
    ) -> None:
        """Remove generated ``_exports*`` files no longer used by codegen."""
        stale_names = (
            c.Infra.ROOT_EXPORTS_FILENAME,
            "_exports_lazy.py",
        )
        search_dirs = {
            plan.context.pkg_dir,
            plan.context.pkg_dir / c.Infra.ROOT_EXPORTS_DIR,
        }
        for base_dir in sorted(search_dirs):
            if not base_dir.is_dir():
                continue
            stale_paths = [
                *(base_dir / name for name in stale_names),
                *base_dir.glob("_exports_lazy_part_*.py"),
            ]
            for path in sorted(stale_paths):
                previous = self._read_generated_file(path)
                if previous is None or not previous.startswith(c.Infra.AUTOGEN_HEADER):
                    continue
                if check_only:
                    self._modified_files.add(str(path))
                    continue
                path.unlink()
                self._modified_files.add(str(path))

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
