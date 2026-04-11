"""Codegen utilities composition for the infrastructure namespace."""

from __future__ import annotations

from pathlib import Path

from flext_infra import (
    FlextInfraUtilitiesCodegenLazyAliases,
    FlextInfraUtilitiesCodegenNamespace,
)


class FlextInfraUtilitiesCodegen(
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCodegenLazyAliases,
):
    """Compose all codegen utility concerns for ``u.Infra``."""

    @staticmethod
    def dir_has_py_files(pkg_dir: Path) -> bool:
        """Return whether a package directory contains canonical Python files."""
        if not pkg_dir.is_dir():
            return False
        return any(
            child.is_file() and child.suffix == ".py" for child in pkg_dir.iterdir()
        )


__all__ = ["FlextInfraUtilitiesCodegen"]
