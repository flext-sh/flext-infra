"""Export scanning and package discovery for lazy-init generation.

Scans sibling .py files for ``__all__`` and AST definitions, discovers
package directories, and merges child exports bottom-up.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import re
from collections.abc import Mapping, MutableSequence
from pathlib import Path
from typing import ClassVar

from flext_infra import c, t

from .output import FlextInfraUtilitiesOutput
from .rope_helpers import FlextInfraUtilitiesRopeHelpers

_INFRA_ONLY_EXPORTS: frozenset[str] = frozenset({
    "cleanup_submodule_namespace",
    "install_lazy_exports",
    "lazy_getattr",
    "merge_lazy_imports",
})

_TYPEVAR_CALL_NAMES: frozenset[str] = frozenset({
    "TypeVar",
    "ParamSpec",
    "TypeVarTuple",
})


class FlextInfraUtilitiesCodegenLazyScanning:
    """Export scanning and package discovery helpers."""

    INFRA_ONLY_EXPORTS: ClassVar[frozenset[str]] = _INFRA_ONLY_EXPORTS

    @staticmethod
    def dir_has_py_files(pkg_dir: Path) -> bool:
        """Return True if directory has .py files besides __init__.py."""
        return any(
            f.name != c.Infra.Files.INIT_PY and f.suffix == c.Infra.Extensions.PYTHON
            for f in pkg_dir.iterdir()
            if f.is_file()
        )

    @staticmethod
    def default_docstring(dir_name: str) -> str:
        label = dir_name.replace("_", " ").replace("-", " ").strip()
        return f'"""{label.capitalize()} package."""'

    _DOCSTRING_RE: re.Pattern[str] = re.compile(
        r'\A\s*("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"[^"]*"|\'[^\']*\')',
    )

    @staticmethod
    def read_existing_docstring(init_path: Path) -> str:
        """Read ONLY the docstring from an existing __init__.py."""
        if not init_path.exists():
            return ""
        try:
            content = init_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except OSError:
            return ""
        match = FlextInfraUtilitiesCodegenLazyScanning._DOCSTRING_RE.match(content)
        if match:
            return match.group(1)
        return ""

    @staticmethod
    def build_sibling_export_index(
        pkg_dir: Path,
        current_pkg: str,
    ) -> t.Infra.MutableLazyImportMap:
        """Scan sibling .py files for exports (including nested submodules)."""
        index: t.Infra.MutableLazyImportMap = {}
        for py_file in sorted(pkg_dir.rglob("*.py")):
            FlextInfraUtilitiesCodegenLazyScanning._index_single_file(
                py_file,
                pkg_dir,
                current_pkg,
                index,
            )
        return index

    @staticmethod
    def _index_single_file(
        py_file: Path,
        pkg_dir: Path,
        current_pkg: str,
        index: t.Infra.MutableLazyImportMap,
    ) -> None:
        """Index exports from a single .py file into the lazy map."""
        if py_file.name in {c.Infra.Files.INIT_PY, "__main__.py", "__version__.py"}:
            return
        sibling_package_init = py_file.parent / py_file.stem / c.Infra.Files.INIT_PY
        if sibling_package_init.exists():
            return
        rel_path = py_file.relative_to(pkg_dir)
        if (
            len(rel_path.parts) == 1
            and py_file.name.startswith("_")
            and "." not in current_pkg
        ):
            return
        if py_file.stem[0:1].isdigit():
            return
        mod_parts = rel_path.with_suffix("").parts
        mod_stem = ".".join(mod_parts)
        mod_path = f"{current_pkg}.{mod_stem}" if current_pkg else mod_stem
        if len(rel_path.parts) == 1 and py_file.stem not in index:
            index[py_file.stem] = (mod_path, "")
        try:
            source = py_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except OSError:
            FlextInfraUtilitiesOutput.warning(f"skipping {py_file.name}: read failed")
            return

        has_all = False
        all_exports: list[str] = []
        for (
            name,
            value_str,
        ) in FlextInfraUtilitiesRopeHelpers.get_module_level_assignments(source):
            if name == c.Infra.Dunders.ALL:
                has_all = True
                words = re.findall(r'["\']([^"\']+)["\']', value_str)
                all_exports.extend(words)

        if has_all and all_exports:
            for name in all_exports:
                if name not in index and name not in _INFRA_ONLY_EXPORTS:
                    index[name] = (mod_path, name)
        else:
            FlextInfraUtilitiesCodegenLazyScanning._scan_public_defs(
                source,
                mod_path,
                index,
            )

    @staticmethod
    def _scan_public_defs(
        source: str,
        mod_path: str,
        index: t.Infra.MutableLazyImportMap,
    ) -> None:
        try:
            module = ast.parse(source)
        except SyntaxError:
            return

        names: list[str] = []
        for node in module.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                names.append(node.name)
                continue
            if isinstance(node, ast.Assign):
                names.extend(
                    target.id for target in node.targets if isinstance(target, ast.Name)
                )
                continue
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names.append(node.target.id)

        for name in names:
            if not name.startswith("_"):
                index[name] = (mod_path, name)

    _TYPEVAR_ASSIGN_RE: re.Pattern[str] = re.compile(
        r"^(\w+)\s*=\s*(?:TypeVar|ParamSpec|TypeVarTuple)\s*\(",
        re.MULTILINE,
    )

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
        for match in FlextInfraUtilitiesCodegenLazyScanning._TYPEVAR_ASSIGN_RE.finditer(
            source,
        ):
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
        children: MutableSequence[str] = []
        for subdir in sorted(pkg_dir.iterdir()):
            if not subdir.is_dir() or subdir.name.startswith("."):
                continue
            if str(subdir) not in dir_exports:
                continue
            child_pkg = f"{current_pkg}.{subdir.name}" if current_pkg else subdir.name
            children.append(child_pkg)
        return children

    @staticmethod
    def collect_descendant_packages(
        pkg_dir: Path,
        current_pkg: str,
        dir_exports: Mapping[str, t.Infra.LazyImportMap],
    ) -> t.StrSequence:
        descendants: MutableSequence[str] = []
        for subdir_key in sorted(dir_exports):
            subdir_path = Path(subdir_key)
            if subdir_path == pkg_dir or pkg_dir not in subdir_path.parents:
                continue
            rel_parts = subdir_path.relative_to(pkg_dir).parts
            if not rel_parts:
                continue
            descendant_pkg = (
                ".".join((current_pkg, *rel_parts))
                if current_pkg
                else ".".join(rel_parts)
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
            FlextInfraUtilitiesCodegenLazyScanning._merge_single_child(
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
        if subdir.name != c.Infra.Dunders.INIT and subdir.name not in lazy_map:
            submodule = f"{current_pkg}.{subdir.name}" if current_pkg else subdir.name
            lazy_map[subdir.name] = (submodule, "")
        for name, (mod, attr) in sub_exports.items():
            if (
                FlextInfraUtilitiesCodegenLazyScanning.should_bubble_up(name)
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

        ver_mod = f"{current_pkg}.__version__" if current_pkg else "__version__"
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


__all__ = ["FlextInfraUtilitiesCodegenLazyScanning"]
