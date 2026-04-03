"""Child/descendant package collection, export merging, and version extraction.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Mapping, MutableSequence
from pathlib import Path

from flext_infra import c, t

from .rope_helpers import FlextInfraUtilitiesRopeHelpers

_INFRA_ONLY_EXPORTS: frozenset[str] = frozenset({
    "cleanup_submodule_namespace",
    "install_lazy_exports",
    "lazy_getattr",
    "merge_lazy_imports",
})

_TYPEVAR_ASSIGN_RE: re.Pattern[str] = re.compile(
    r"^(\w+)\s*=\s*(?:TypeVar|ParamSpec|TypeVarTuple)\s*\(",
    re.MULTILINE,
)


class FlextInfraUtilitiesCodegenLazyMerging:
    """Child/descendant package collection and export merging helpers."""

    @staticmethod
    def detect_eager_typevar_names(pkg_dir: Path) -> t.Infra.StrSet:
        """Detect module-level TypeVar/ParamSpec names in typings.py."""
        typings_file = pkg_dir / c.Infra.Files.TYPINGS_PY
        if not typings_file.exists():
            return set()
        try:
            source = typings_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except OSError:
            return set()
        names: t.Infra.StrSet = set()
        for match in _TYPEVAR_ASSIGN_RE.finditer(source):
            name = match.group(1)
            if not name.startswith("_"):
                names.add(name)
        return names

    @staticmethod
    def should_bubble_up(name: str) -> bool:
        """Check if an export should bubble up to the parent package."""
        if name.startswith("_") or name in {c.Infra.Dunders.INIT, "main"}:
            return False
        if name in _INFRA_ONLY_EXPORTS:
            return False
        return not name.isupper()

    @staticmethod
    def collect_child_packages(
        pkg_dir: Path,
        current_pkg: str,
        dir_exports: Mapping[str, t.Infra.LazyImportMap],
    ) -> t.StrSequence:
        """Collect importable child package names from subdirectories."""
        from .codegen_lazy_scanning import (  # noqa: PLC0415
            FlextInfraUtilitiesCodegenLazyScanning,
        )

        children: MutableSequence[str] = []
        for subdir in sorted(pkg_dir.iterdir()):
            if not subdir.is_dir() or subdir.name.startswith("."):
                continue
            if str(subdir) not in dir_exports:
                continue
            child_pkg = (
                FlextInfraUtilitiesCodegenLazyScanning._package_name_from_rel_parts(  # noqa: SLF001
                    rel_parts=(subdir.name,),
                    current_pkg=current_pkg,
                    is_project_root=(pkg_dir / "pyproject.toml").exists(),
                )
            )
            children.append(child_pkg)
        return children

    @staticmethod
    def collect_descendant_packages(
        pkg_dir: Path,
        current_pkg: str,
        dir_exports: Mapping[str, t.Infra.LazyImportMap],
    ) -> t.StrSequence:
        """Collect importable descendant package names from dir_exports."""
        from .codegen_lazy_scanning import (  # noqa: PLC0415
            FlextInfraUtilitiesCodegenLazyScanning,
        )

        descendants: MutableSequence[str] = []
        for subdir_key in sorted(dir_exports):
            subdir_path = Path(subdir_key)
            if subdir_path == pkg_dir or pkg_dir not in subdir_path.parents:
                continue
            rel_parts = subdir_path.relative_to(pkg_dir).parts
            if not rel_parts:
                continue
            descendant_pkg = (
                FlextInfraUtilitiesCodegenLazyScanning._package_name_from_rel_parts(  # noqa: SLF001
                    rel_parts=rel_parts,
                    current_pkg=current_pkg,
                    is_project_root=(pkg_dir / "pyproject.toml").exists(),
                )
            )
            descendants.append(descendant_pkg)
        return descendants

    @staticmethod
    def merge_child_exports(
        pkg_dir: Path,
        current_pkg: str,
        lazy_map: t.Infra.MutableLazyImportMap,
        dir_exports: Mapping[str, t.Infra.LazyImportMap],
    ) -> None:
        """Merge child subdirectory exports into parent's lazy map."""
        for subdir in sorted(pkg_dir.iterdir()):
            if not subdir.is_dir() or subdir.name.startswith("."):
                continue
            subdir_key = str(subdir)
            if subdir_key not in dir_exports:
                continue
            FlextInfraUtilitiesCodegenLazyMerging._merge_single_child(
                subdir,
                current_pkg,
                lazy_map,
                dir_exports[subdir_key],
            )

    @staticmethod
    def _merge_single_child(
        subdir: Path,
        current_pkg: str,
        lazy_map: t.Infra.MutableLazyImportMap,
        sub_exports: t.Infra.LazyImportMap,
    ) -> None:
        from .codegen_lazy_scanning import (  # noqa: PLC0415
            FlextInfraUtilitiesCodegenLazyScanning,
        )

        is_project_root = False
        if hasattr(subdir.parent, "joinpath"):
            is_project_root = (subdir.parent / "pyproject.toml").exists()

        if subdir.name != c.Infra.Dunders.INIT and subdir.name not in lazy_map:
            submodule = (
                FlextInfraUtilitiesCodegenLazyScanning._package_name_from_rel_parts(  # noqa: SLF001
                    rel_parts=(subdir.name,),
                    current_pkg=current_pkg,
                    is_project_root=is_project_root,
                )
            )
            lazy_map[subdir.name] = (submodule, "")
        for name, (mod, attr) in sub_exports.items():
            if (
                FlextInfraUtilitiesCodegenLazyMerging.should_bubble_up(name)
                and name not in lazy_map
            ):
                lazy_map[name] = (mod, attr)

    @staticmethod
    def extract_version_exports(
        pkg_dir: Path,
        current_pkg: str,
    ) -> t.Infra.VersionExportsResult:
        """Extract version-related exports from __version__.py."""
        ver_file = pkg_dir / "__version__.py"
        if not ver_file.exists():
            return ({}, {})
        try:
            source = ver_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except OSError:
            return ({}, {})

        assignments = FlextInfraUtilitiesRopeHelpers.get_module_level_assignments(
            source
        )
        inline = {
            name: re.sub(r"""^['"]|['"]$""", "", val)
            for name, val in assignments
            if val.startswith(("'", '"'))
        }

        ver_mod = (
            f"{current_pkg}.{c.Infra.Dunders.VERSION}"
            if current_pkg
            else c.Infra.Dunders.VERSION
        )
        eager: t.Infra.MutableLazyImportMap = {}
        has_all = False
        exported_names: list[str] = []
        for name, value_str in assignments:
            if name == c.Infra.Dunders.ALL:
                has_all = True
                words = re.findall(r'["\']([^"\']+)["\']', value_str)
                exported_names.extend(words)
        if has_all and exported_names:
            for name in exported_names:
                if name not in inline:
                    eager[name] = (ver_mod, name)
            return (inline, eager)
        for name, _value_str in assignments:
            if name.startswith("__") and name.endswith("__") and name not in inline:
                eager[name] = (ver_mod, name)
        return (inline, eager)


__all__ = ["FlextInfraUtilitiesCodegenLazyMerging"]
