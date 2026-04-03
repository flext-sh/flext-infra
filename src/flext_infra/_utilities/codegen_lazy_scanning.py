"""Export scanning and package discovery for lazy-init generation.

Scans sibling .py files for ``__all__`` and AST definitions, discovers
package directories, and merges child exports bottom-up.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import ClassVar

from flext_infra import c, t

from .codegen_lazy_merging import FlextInfraUtilitiesCodegenLazyMerging
from .output import FlextInfraUtilitiesOutput
from .rope_helpers import FlextInfraUtilitiesRopeHelpers

_INFRA_ONLY_EXPORTS: frozenset[str] = frozenset({
    "cleanup_submodule_namespace",
    "install_lazy_exports",
    "lazy_getattr",
    "merge_lazy_imports",
})


class FlextInfraUtilitiesCodegenLazyScanning(
    FlextInfraUtilitiesCodegenLazyMerging,
):
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
        for py_file in sorted(pkg_dir.rglob(c.Infra.Extensions.PYTHON_GLOB)):
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
        if FlextInfraUtilitiesCodegenLazyScanning._skip_wrapper_root_file(
            rel_path=rel_path,
            pkg_dir=pkg_dir,
            current_pkg=current_pkg,
        ):
            return
        if (
            len(rel_path.parts) == 1
            and py_file.name.startswith("_")
            and "." not in current_pkg
        ):
            return
        if py_file.stem[0:1].isdigit():
            return
        mod_path = FlextInfraUtilitiesCodegenLazyScanning._module_path_from_rel_path(
            rel_path=rel_path,
            current_pkg=current_pkg,
            is_project_root=(pkg_dir / "pyproject.toml").exists(),
        )
        if not mod_path:
            return
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
    def _skip_wrapper_root_file(
        *,
        rel_path: Path,
        pkg_dir: Path,
        current_pkg: str,
    ) -> bool:
        """Skip loose project-root files when generating a wrapper package."""
        if not current_pkg or len(rel_path.parts) != 1:
            return False
        current_pkg_path = Path(*current_pkg.split("."))
        namespaced_src_dir = pkg_dir / c.Infra.Paths.DEFAULT_SRC_DIR / current_pkg_path
        return namespaced_src_dir.exists()

    @staticmethod
    def _module_path_from_rel_path(
        rel_path: Path,
        current_pkg: str,
        *,
        is_project_root: bool = False,
    ) -> str:
        """Normalize a scanned file path into the importable module path."""
        rel_parts = rel_path.with_suffix("").parts
        if not rel_parts:
            return ""

        root_segment = rel_parts[0]
        if is_project_root and root_segment in {
            c.Infra.Paths.DEFAULT_SRC_DIR,
            c.Infra.Directories.TESTS,
            c.Infra.Directories.EXAMPLES,
            c.Infra.Directories.SCRIPTS,
        }:
            return FlextInfraUtilitiesCodegenLazyScanning._rooted_module_path(
                rel_parts=rel_parts,
                current_pkg=current_pkg,
            )

        mod_stem = ".".join(rel_parts)
        return f"{current_pkg}.{mod_stem}" if current_pkg else mod_stem

    @staticmethod
    def _rooted_module_path(
        *,
        rel_parts: tuple[str, ...],
        current_pkg: str,
    ) -> str:
        """Build module path for project-root wrapper packages."""
        root_segment = rel_parts[0]
        remaining_parts = rel_parts[1:]
        if root_segment == c.Infra.Paths.DEFAULT_SRC_DIR:
            current_pkg_parts = tuple(part for part in current_pkg.split(".") if part)
            if remaining_parts[: len(current_pkg_parts)] == current_pkg_parts:
                remaining_parts = remaining_parts[len(current_pkg_parts) :]
            module_parts = (*current_pkg_parts, *remaining_parts)
            return ".".join(part for part in module_parts if part)
        module_parts = (root_segment, *remaining_parts)
        return ".".join(part for part in module_parts if part)

    @staticmethod
    def _package_name_from_rel_parts(
        *,
        rel_parts: tuple[str, ...],
        current_pkg: str,
        is_project_root: bool = False,
    ) -> str:
        """Normalize a descendant package path relative to the current package dir."""
        if not rel_parts:
            return current_pkg
        root_segment = rel_parts[0]
        if is_project_root and root_segment in {
            c.Infra.Paths.DEFAULT_SRC_DIR,
            c.Infra.Directories.TESTS,
            c.Infra.Directories.EXAMPLES,
            c.Infra.Directories.SCRIPTS,
        }:
            return FlextInfraUtilitiesCodegenLazyScanning._rooted_module_path(
                rel_parts=rel_parts,
                current_pkg=current_pkg,
            )
        package_parts = (
            *tuple(part for part in current_pkg.split(".") if part),
            *rel_parts,
        )
        return ".".join(part for part in package_parts if part)

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


__all__ = ["FlextInfraUtilitiesCodegenLazyScanning"]
