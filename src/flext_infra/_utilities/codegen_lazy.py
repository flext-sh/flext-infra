"""Lazy-init generation: scanning, merging, and alias resolution.

Unified implementation for child collection, export merging, package
discovery, version extraction, and single-letter alias resolution.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import re
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar

from flext_infra import (
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesIteration,
    c,
    t,
)

from .reporting import FlextInfraUtilitiesReporting
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
_ROOT_WRAPPER_SEGMENTS: frozenset[str] = frozenset({
    c.Infra.Directories.DOCS,
    c.Infra.Paths.DEFAULT_SRC_DIR,
    c.Infra.Directories.TESTS,
    c.Infra.Directories.EXAMPLES,
    c.Infra.Directories.SCRIPTS,
})

_CORE_RUNTIME_ALIAS_TARGETS: dict[str, t.Infra.StrPair] = {
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "x": ("flext_core.mixins", "FlextMixins"),
}


# =====================================================================
# Merging — child/descendant collection, export merging
# =====================================================================


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
        children: MutableSequence[str] = []
        for subdir in sorted(pkg_dir.iterdir()):
            if not subdir.is_dir() or subdir.name.startswith("."):
                continue
            if str(subdir) not in dir_exports:
                continue
            child_pkg = (
                FlextInfraUtilitiesCodegenLazyScanning.package_name_from_rel_parts(
                    rel_parts=(subdir.name,),
                    current_pkg=current_pkg,
                    is_project_root=(
                        pkg_dir / c.Infra.Files.PYPROJECT_FILENAME
                    ).exists(),
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
        descendants: MutableSequence[str] = []
        for subdir_key in sorted(dir_exports):
            subdir_path = Path(subdir_key)
            if subdir_path == pkg_dir or pkg_dir not in subdir_path.parents:
                continue
            rel_parts = subdir_path.relative_to(pkg_dir).parts
            if not rel_parts:
                continue
            descendant_pkg = (
                FlextInfraUtilitiesCodegenLazyScanning.package_name_from_rel_parts(
                    rel_parts=rel_parts,
                    current_pkg=current_pkg,
                    is_project_root=(
                        pkg_dir / c.Infra.Files.PYPROJECT_FILENAME
                    ).exists(),
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
        is_project_root = False
        if hasattr(subdir.parent, "joinpath"):
            is_project_root = (
                subdir.parent / c.Infra.Files.PYPROJECT_FILENAME
            ).exists()

        if subdir.name != c.Infra.Dunders.INIT and subdir.name not in lazy_map:
            submodule = (
                FlextInfraUtilitiesCodegenLazyScanning.package_name_from_rel_parts(
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


# =====================================================================
# Scanning — export scanning and package discovery
# =====================================================================


class FlextInfraUtilitiesCodegenLazyScanning(
    FlextInfraUtilitiesCodegenLazyMerging,
):
    """Export scanning and package discovery helpers."""

    INFRA_ONLY_EXPORTS: ClassVar[frozenset[str]] = _INFRA_ONLY_EXPORTS

    @staticmethod
    def dir_has_py_files(pkg_dir: Path) -> bool:
        """Return True if directory has .py files besides __init__.py."""
        return any(
            f.name != c.Infra.Files.INIT_PY
            and FlextInfraUtilitiesIteration.is_canonical_python_file(f)
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
            if not FlextInfraUtilitiesIteration.is_canonical_python_file(py_file):
                continue
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
        if not FlextInfraUtilitiesIteration.is_canonical_python_file(py_file):
            return
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
            is_project_root=(pkg_dir / c.Infra.Files.PYPROJECT_FILENAME).exists(),
        )
        if not mod_path:
            return
        if len(rel_path.parts) == 1 and py_file.stem not in index:
            index[py_file.stem] = (mod_path, "")
        try:
            source = py_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except OSError:
            FlextInfraUtilitiesReporting.warning(
                f"skipping {py_file.name}: read failed",
            )
            return

        has_all = False
        all_exports: MutableSequence[str] = []
        for (
            name,
            value_str,
        ) in FlextInfraUtilitiesRopeHelpers.get_module_level_assignments(source):
            if name == c.Infra.Dunders.ALL:
                has_all = True
                words = re.findall(r'["\']([^"\']+)["\']', value_str)
                all_exports.extend(words)

        if has_all:
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
        if is_project_root and root_segment in _ROOT_WRAPPER_SEGMENTS:
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
    def package_name_from_rel_parts(
        *,
        rel_parts: tuple[str, ...],
        current_pkg: str,
        is_project_root: bool = False,
    ) -> str:
        """Normalize a descendant package path relative to the current package dir."""
        if not rel_parts:
            return current_pkg
        root_segment = rel_parts[0]
        if is_project_root and root_segment in _ROOT_WRAPPER_SEGMENTS:
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


# =====================================================================
# Aliases — single-letter alias resolution
# =====================================================================


class FlextInfraUtilitiesCodegenLazyAliases:
    """Resolves single-letter aliases from ALIAS_TO_SUFFIX mapping."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        self._root = (
            workspace_root
            if workspace_root is not None
            else FlextInfraUtilitiesDiscovery.discover_workspace_root_from_file(
                Path(__file__)
            )
        )
        self._alias_target_cache: MutableMapping[
            tuple[str, str],
            t.Infra.StrPair | None,
        ] = {}
        self._package_dir_cache: MutableMapping[
            tuple[str, str],
            Path | None,
        ] = {}

    def resolve_aliases(
        self,
        lazy_map: t.Infra.MutableLazyImportMap,
        *,
        pkg_dir: Path,
    ) -> None:
        """Resolve single-letter aliases from ALIAS_TO_SUFFIX mapping."""
        current_pkg = FlextInfraUtilitiesDiscovery.discover_package_from_file(
            pkg_dir / c.Infra.Files.INIT_PY
        )
        for alias, suffix in c.Infra.ALIAS_TO_SUFFIX.items():
            expected_module = "typings" if suffix == "Types" else suffix.lower()
            if self._existing_alias_is_canonical(
                lazy_map, alias, suffix, expected_module
            ):
                continue
            if (
                current_pkg == c.Infra.Packages.CORE_UNDERSCORE
                and alias in _CORE_RUNTIME_ALIAS_TARGETS
            ):
                lazy_map[alias] = _CORE_RUNTIME_ALIAS_TARGETS[alias]
                continue
            if alias == "s":
                service_target = self._find_service_target(lazy_map)
                if service_target is not None:
                    lazy_map[alias] = service_target
                    continue
            facade_target = self._find_facade_target(lazy_map, suffix, expected_module)
            if facade_target is not None:
                lazy_map[alias] = facade_target
                continue
            if alias in _CORE_RUNTIME_ALIAS_TARGETS:
                lazy_map[alias] = _CORE_RUNTIME_ALIAS_TARGETS[alias]
                continue
            if alias in lazy_map:
                continue
            parent_target = self._resolve_export_target(
                pkg_dir,
                alias,
                suffix,
                expected_module,
                seen=frozenset(),
            )
            if parent_target is not None:
                lazy_map[alias] = parent_target

    @staticmethod
    def _existing_alias_is_canonical(
        lazy_map: t.Infra.MutableLazyImportMap,
        alias: str,
        suffix: str,
        expected_module: str,
    ) -> bool:
        if alias not in lazy_map:
            return False
        existing = lazy_map[alias]
        existing_basename = existing[0].rsplit(".", 1)[-1]
        return (
            existing[1].endswith(suffix)
            and existing[0].count(".") >= 1
            and existing_basename == expected_module
        )

    @staticmethod
    def _find_facade_target(
        lazy_map: t.Infra.MutableLazyImportMap,
        suffix: str,
        expected_module: str,
    ) -> t.Infra.StrPair | None:
        candidates: MutableSequence[tuple[int, int, str, str]] = []
        for name, (mod, _attr) in list(lazy_map.items()):
            basename = mod.rsplit(".", 1)[-1]
            if (
                name.endswith(suffix)
                and mod.count(".") >= 1
                and basename == expected_module
            ):
                candidates.append((mod.count("."), mod.count("._"), mod, name))
        if not candidates:
            return None
        _depth, _private_count, module_path, export_name = min(candidates)
        return (module_path, export_name)

    @staticmethod
    def _find_service_target(
        lazy_map: t.Infra.MutableLazyImportMap,
    ) -> t.Infra.StrPair | None:
        """Resolve the canonical `s` alias from local public service/base modules."""
        explicit_alias = lazy_map.get("s")
        if explicit_alias is not None and explicit_alias[0].rsplit(".", 1)[-1] in {
            "base",
            "service",
            "api",
        }:
            return explicit_alias
        for module_name, suffixes in (
            ("base", ("CommandContext", "ServiceBase")),
            ("service", ("Service",)),
            ("api", ("Service",)),
        ):
            for name, (mod, _attr) in list(lazy_map.items()):
                if mod.rsplit(".", 1)[-1] != module_name:
                    continue
                if any(name.endswith(suffix) for suffix in suffixes):
                    return (mod, name)
        return None

    @staticmethod
    def _discover_parent_package(pkg_dir: Path) -> str | None:
        """Discover the parent flext package by inspecting constants.py MRO."""
        result = FlextInfraUtilitiesDiscovery.resolve_parent_constants(
            pkg_dir,
            return_module=True,
        )
        if not result or result == c.Infra.Packages.CORE_UNDERSCORE:
            return result or None
        return result.split(".")[0]

    def _resolve_export_target(
        self,
        pkg_dir: Path,
        alias: str,
        suffix: str,
        expected_module: str,
        *,
        seen: frozenset[str],
    ) -> t.Infra.StrPair | None:
        cache_key = (str(pkg_dir), alias)
        if cache_key in self._alias_target_cache:
            return self._alias_target_cache[cache_key]
        pkg_key = str(pkg_dir.resolve())
        if pkg_key in seen:
            return None
        current_pkg = FlextInfraUtilitiesDiscovery.discover_package_from_file(
            pkg_dir / c.Infra.Files.INIT_PY
        )
        if not current_pkg:
            self._alias_target_cache[cache_key] = None
            return None
        local_exports = (
            FlextInfraUtilitiesCodegenLazyScanning.build_sibling_export_index(
                pkg_dir,
                current_pkg,
            )
        )
        target: t.Infra.StrPair | None = None
        if self._existing_alias_is_canonical(
            local_exports, alias, suffix, expected_module
        ):
            target = local_exports[alias]
        else:
            target = self._find_facade_target(local_exports, suffix, expected_module)
        if target is None:
            parent_pkg = self._discover_parent_package(pkg_dir)
            if parent_pkg:
                parent_dir = self._find_package_directory(pkg_dir, parent_pkg)
                if parent_dir is not None:
                    target = self._resolve_export_target(
                        parent_dir,
                        alias,
                        suffix,
                        expected_module,
                        seen=seen | {pkg_key},
                    )
        self._alias_target_cache[cache_key] = target
        return target

    def _find_package_directory(self, pkg_dir: Path, package_name: str) -> Path | None:
        project_root = self._discover_project_root(pkg_dir)
        cache_key = (str(project_root) if project_root else "", package_name)
        if cache_key in self._package_dir_cache:
            return self._package_dir_cache[cache_key]
        candidates: MutableSequence[Path] = []
        if project_root is not None:
            candidates.extend(
                self._build_package_candidates(project_root, package_name)
            )
        candidates.extend(self._build_package_candidates(self._root, package_name))
        candidates.extend(self._build_workspace_package_candidates(package_name))
        resolved: Path | None = None
        seen_candidates: MutableSequence[Path] = []
        for candidate in candidates:
            candidate_resolved = candidate.resolve()
            if candidate_resolved in seen_candidates:
                continue
            seen_candidates.append(candidate_resolved)
            if candidate.is_dir():
                resolved = candidate
                break
        self._package_dir_cache[cache_key] = resolved
        return resolved

    @staticmethod
    def _discover_project_root(pkg_dir: Path) -> Path | None:
        for candidate in (pkg_dir, *pkg_dir.parents):
            if (candidate / c.Infra.Files.PYPROJECT_FILENAME).is_file():
                return candidate
        return None

    @staticmethod
    def _build_package_candidates(base_dir: Path, package_name: str) -> Sequence[Path]:
        package_path = Path(*package_name.split("."))
        root_segment = package_path.parts[0] if package_path.parts else ""
        candidates: MutableSequence[Path] = []
        if root_segment in _ROOT_WRAPPER_SEGMENTS:
            candidates.append(base_dir / package_path)
        candidates.append(base_dir / c.Infra.Paths.DEFAULT_SRC_DIR / package_path)
        if root_segment not in _ROOT_WRAPPER_SEGMENTS:
            candidates.extend([
                base_dir / c.Infra.Directories.DOCS / package_path,
                base_dir / c.Infra.Directories.TESTS / package_path,
                base_dir / c.Infra.Directories.EXAMPLES / package_path,
                base_dir / c.Infra.Directories.SCRIPTS / package_path,
            ])
        return tuple(candidates)

    def _build_workspace_package_candidates(self, package_name: str) -> Sequence[Path]:
        package_path = Path(*package_name.split("."))
        root_segment = package_path.parts[0] if package_path.parts else ""
        patterns: MutableSequence[str] = []
        if root_segment in _ROOT_WRAPPER_SEGMENTS:
            patterns.append(str(Path("*") / package_path))
        else:
            patterns.append(
                str(Path("*") / c.Infra.Paths.DEFAULT_SRC_DIR / package_path)
            )
        if root_segment not in _ROOT_WRAPPER_SEGMENTS:
            patterns.extend([
                str(Path("*") / c.Infra.Directories.DOCS / package_path),
                str(Path("*") / c.Infra.Directories.TESTS / package_path),
                str(Path("*") / c.Infra.Directories.EXAMPLES / package_path),
                str(Path("*") / c.Infra.Directories.SCRIPTS / package_path),
            ])
        candidates: MutableSequence[Path] = []
        for pattern in patterns:
            candidates.extend(sorted(self._root.glob(pattern)))
        return tuple(candidates)


__all__ = [
    "FlextInfraUtilitiesCodegenLazyAliases",
    "FlextInfraUtilitiesCodegenLazyMerging",
    "FlextInfraUtilitiesCodegenLazyScanning",
]
