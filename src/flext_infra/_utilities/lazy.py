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

from flext_infra import (
    FlextInfraUtilitiesCodegenGeneration,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesReporting,
    FlextInfraUtilitiesRope,
    c,
    t,
)

# =====================================================================
# Merging — child/descendant collection, export merging
# =====================================================================


class FlextInfraUtilitiesCodegenLazyMerging:
    """Child/descendant package collection and export merging helpers."""

    @classmethod
    def _register_export(
        cls,
        index: t.Infra.MutableLazyImportMap,
        name: str,
        target: t.Infra.StrPair,
    ) -> None:
        """Register one export or raise when another module already owns it."""
        existing = index.get(name)
        if existing is None:
            index[name] = target
            return
        if existing == target:
            return
        existing_target = f"{existing[0]}.{existing[1]}".rstrip(".")
        target_value = f"{target[0]}.{target[1]}".rstrip(".")
        msg = f"export collision for {name!r}: {existing_target} != {target_value}"
        raise ValueError(
            msg,
        )

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
            child_pkg = FlextInfraUtilitiesCodegenLazyScanning.import_path_from_rel_parts(
                rel_parts=(subdir.name,),
                current_pkg=current_pkg,
                is_project_root=(pkg_dir / c.Infra.Files.PYPROJECT_FILENAME).exists(),
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
                FlextInfraUtilitiesCodegenLazyScanning.import_path_from_rel_parts(
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
                lazy_map,
                dir_exports[subdir_key],
            )

    @staticmethod
    def _merge_single_child(
        lazy_map: t.Infra.MutableLazyImportMap,
        sub_exports: t.Infra.LazyImportMap,
    ) -> None:
        for name, (mod, attr) in sub_exports.items():
            if not attr:
                continue
            if (
                not name.startswith("_")
                and name not in {c.Infra.Dunders.INIT, "main"}
                and name not in c.Infra.ALIAS_NAMES
                and name not in c.Infra.INFRA_ONLY_EXPORTS
                and not name.isupper()
            ):
                FlextInfraUtilitiesCodegenLazyMerging._register_export(
                    lazy_map,
                    name,
                    (mod, attr),
                )

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

        assignments = FlextInfraUtilitiesRope.get_module_level_assignments(source)
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


class FlextInfraUtilitiesCodegenLazyScanning(FlextInfraUtilitiesCodegenLazyMerging):
    """Export scanning and package discovery helpers."""

    @staticmethod
    def dir_has_py_files(pkg_dir: Path) -> bool:
        """Return True if directory has .py files besides __init__.py."""
        return any(
            f.name != c.Infra.Files.INIT_PY
            and FlextInfraUtilitiesIteration.is_canonical_python_file(f)
            for f in pkg_dir.iterdir()
            if f.is_file()
        )

    @classmethod
    def build_sibling_export_index(
        cls,
        pkg_dir: Path,
        current_pkg: str,
    ) -> t.Infra.MutableLazyImportMap:
        """Scan sibling .py files for exports through one shared Rope project."""
        index: t.Infra.MutableLazyImportMap = {}
        project_root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(
            pkg_dir / c.Infra.Files.INIT_PY,
        )
        rope_root = project_root.parent if project_root is not None else pkg_dir
        with FlextInfraUtilitiesRope.open_project(rope_root) as rope_project:
            for py_file in sorted(pkg_dir.rglob(c.Infra.Extensions.PYTHON_GLOB)):
                if not FlextInfraUtilitiesIteration.is_canonical_python_file(py_file):
                    continue
                cls._index_single_file(
                    py_file,
                    pkg_dir,
                    current_pkg,
                    index,
                    rope_project,
                )
        return index

    @classmethod
    def _index_single_file(
        cls,
        py_file: Path,
        pkg_dir: Path,
        current_pkg: str,
        index: t.Infra.MutableLazyImportMap,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        """Index exports from a single .py file into the lazy map."""
        if not FlextInfraUtilitiesIteration.is_canonical_python_file(py_file):
            return
        if py_file.name in {c.Infra.Files.INIT_PY, "__main__.py", "__version__.py"}:
            return
        if FlextInfraUtilitiesCodegenLazyScanning._belongs_to_nested_package(
            py_file=py_file,
            pkg_dir=pkg_dir,
        ):
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
        if FlextInfraUtilitiesCodegenLazyScanning._should_skip_private_module(
            py_file=py_file,
            current_pkg=current_pkg,
        ):
            return
        if py_file.stem[0:1].isdigit():
            return
        mod_path = FlextInfraUtilitiesCodegenLazyScanning.import_path_from_rel_parts(
            rel_parts=rel_path.with_suffix("").parts,
            current_pkg=current_pkg,
            is_project_root=(pkg_dir / c.Infra.Files.PYPROJECT_FILENAME).exists(),
        )
        if not mod_path:
            return
        resource = FlextInfraUtilitiesRope.get_resource_from_path(rope_project, py_file)
        if resource is None:
            FlextInfraUtilitiesReporting.warning(
                f"skipping {py_file.name}: rope resource unavailable",
            )
            return
        source = resource.read()
        all_exports = cls._all_exports_from_source(source)
        policy = FlextInfraUtilitiesCodegenNamespace.module_policy(
            py_file,
            rel_path=rel_path,
            current_pkg=current_pkg,
        )
        if not policy.export_symbols:
            cls._register_export(index, py_file.stem, (mod_path, ""))
            return
        is_root_package = (
            FlextInfraUtilitiesCodegenGeneration.is_root_namespace_package(current_pkg)
        )
        try:
            local_targets = cls._public_defined_targets(
                rope_project=rope_project,
                resource=resource,
                source=source,
                mod_path=mod_path,
                py_file=py_file,
            )
        except FlextInfraUtilitiesRope.SYNTAX_ERRORS:
            FlextInfraUtilitiesReporting.warning(
                f"skipping {py_file.name}: syntax error",
            )
            return
        if all_exports:
            explicit_targets = cls._explicit_reexport_targets(
                rope_project=rope_project,
                resource=resource,
                all_exports=all_exports,
                local_targets=local_targets,
            )
            for export_name in all_exports:
                if not cls._should_publish_symbol(
                    export_name,
                    mod_path=mod_path,
                    py_file=py_file,
                ):
                    continue
                cls._register_export(
                    index,
                    export_name,
                    explicit_targets.get(
                        export_name,
                        local_targets.get(export_name, (mod_path, export_name)),
                    ),
            )
            return
        if not local_targets and not policy.enforce_contract and not is_root_package:
            cls._register_export(index, py_file.stem, (mod_path, ""))
            return
        for export_name, target in local_targets.items():
            cls._register_export(index, export_name, target)

    @staticmethod
    def _all_exports_from_source(source: str) -> tuple[str, ...]:
        """Return ordered names declared in ``__all__``."""
        for name, value_str in FlextInfraUtilitiesRope.get_module_level_assignments(
            source,
        ):
            if name != c.Infra.Dunders.ALL:
                continue
            return tuple(
                dict.fromkeys(re.findall(r'["\']([^"\']+)["\']', value_str)),
            )
        return ()

    @classmethod
    def _public_defined_targets(
        cls,
        *,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        source: str,
        mod_path: str,
        py_file: Path,
    ) -> t.Infra.MutableLazyImportMap:
        """Return public module-local export targets discovered through Rope."""
        assignments = dict(FlextInfraUtilitiesRope.get_module_level_assignments(source))
        targets: t.Infra.MutableLazyImportMap = {
            symbol.name: (mod_path, symbol.name)
            for symbol in FlextInfraUtilitiesRope.get_module_symbols(
                rope_project,
                resource,
            )
            if cls._should_publish_local_symbol(
                symbol.name,
                symbol.kind,
                assignments=assignments,
                mod_path=mod_path,
                py_file=py_file,
            )
        }
        for name, value_str in assignments.items():
            if not cls._should_publish_symbol(name, mod_path=mod_path, py_file=py_file):
                continue
            root_name = cls._assignment_root_name(value_str)
            if root_name in targets:
                targets.setdefault(name, (mod_path, name))
        return targets

    @classmethod
    def _should_publish_local_symbol(
        cls,
        name: str,
        kind: str,
        *,
        assignments: Mapping[str, str],
        mod_path: str,
        py_file: Path,
    ) -> bool:
        if not cls._should_publish_symbol(name, mod_path=mod_path, py_file=py_file):
            return False
        if kind != "assignment":
            return True
        callable_name = cls._assignment_callable_name(assignments.get(name, ""))
        parts = tuple(part for part in mod_path.split(".") if part)
        return (
            callable_name not in c.Infra.TYPEVAR_CALLABLES
            or (bool(parts)
            and (parts[-1] == "typings" or "_typings" in parts))
        )

    @staticmethod
    def _assignment_callable_name(value_str: str) -> str:
        """Return the callable name for a simple assignment expression."""
        match = re.match(r"([A-Za-z_][\w.]*)\s*\(", value_str)
        return match.group(1).rsplit(".", maxsplit=1)[-1] if match else ""

    @classmethod
    def _assignment_root_name(cls, value_str: str) -> str:
        """Return the root local symbol referenced by a module-level assignment."""
        try:
            node = ast.parse(value_str, mode="eval").body
        except SyntaxError:
            return ""
        while isinstance(node, ast.Call):
            node = node.func
        while isinstance(node, ast.Attribute):
            node = node.value
        return node.id if isinstance(node, ast.Name) else ""

    @classmethod
    def _should_publish_symbol(
        cls,
        name: str,
        *,
        mod_path: str,
        py_file: Path,
    ) -> bool:
        """Apply the canonical export filters shared by Rope discovery paths."""
        if name.startswith("_") or name in c.Infra.INFRA_ONLY_EXPORTS:
            return False
        if mod_path.startswith("tests.") and name == "pytestmark":
            return False
        return (
            name != "main"
            or FlextInfraUtilitiesCodegenNamespace.module_policy(
                py_file,
            ).allow_main_export
        )

    @classmethod
    def _explicit_reexport_targets(
        cls,
        *,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        all_exports: Sequence[str],
        local_targets: Mapping[str, t.Infra.StrPair],
    ) -> dict[str, t.Infra.StrPair]:
        """Resolve imported names in ``__all__`` back to their semantic targets."""
        imported = FlextInfraUtilitiesRope.get_semantic_module_imports(
            rope_project,
            resource,
        )
        local_names = frozenset(local_targets)
        return {
            export_name: cls._semantic_target_to_lazy_target(
                rope_project,
                semantic_target,
            )
            for export_name in all_exports
            if export_name not in local_names
            and (semantic_target := imported.get(export_name))
        }

    @staticmethod
    def _semantic_target_to_lazy_target(
        rope_project: t.Infra.RopeProject,
        semantic_target: str,
    ) -> t.Infra.StrPair:
        """Normalize one Rope semantic target to a lazy import target tuple."""
        if rope_project.find_module(semantic_target):
            return (semantic_target, "")
        module_name, _, attr_name = semantic_target.rpartition(".")
        return (module_name, attr_name) if module_name else (semantic_target, "")

    @staticmethod
    def _should_skip_private_module(
        *,
        py_file: Path,
        current_pkg: str,
    ) -> bool:
        """Skip private modules except sanctioned family/implementation packages."""
        if not py_file.stem.startswith("_"):
            return False
        if py_file.name in {
            c.Infra.Files.INIT_PY,
            "__main__.py",
            "__version__.py",
        }:
            return False
        parts = tuple(part for part in current_pkg.split(".") if part)
        if any(part in c.Infra.FAMILY_DIRECTORIES.values() for part in parts):
            return False
        if "services" in parts:
            return True
        if parts and parts[0] in {
            c.Infra.Directories.TESTS,
            c.Infra.Directories.EXAMPLES,
            c.Infra.Directories.SCRIPTS,
        }:
            return True
        return FlextInfraUtilitiesCodegenGeneration.is_root_namespace_package(
            current_pkg
        )

    @staticmethod
    def _belongs_to_nested_package(
        *,
        py_file: Path,
        pkg_dir: Path,
    ) -> bool:
        """Return True when a file belongs to a child package with its own __init__."""
        current = py_file.parent
        while current != pkg_dir:
            if (current / c.Infra.Files.INIT_PY).exists():
                return True
            current = current.parent
        return False

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
    def import_path_from_rel_parts(
        rel_parts: tuple[str, ...],
        current_pkg: str,
        *,
        is_project_root: bool = False,
    ) -> str:
        """Normalize a scanned relative path into an importable package/module path."""
        if not rel_parts:
            return current_pkg

        root_segment = rel_parts[0]
        if is_project_root and root_segment in c.Infra.ROOT_WRAPPER_SEGMENTS:
            return FlextInfraUtilitiesCodegenLazyScanning._rooted_module_path(
                rel_parts=rel_parts,
                current_pkg=current_pkg,
            )

        return ".".join(
            (
                *tuple(part for part in current_pkg.split(".") if part),
                *rel_parts,
            ),
        )

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


# =====================================================================
# Aliases — single-letter alias resolution
# =====================================================================


class FlextInfraUtilitiesCodegenLazyAliases:
    """Resolve inherited public aliases across the package ancestry chain."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        self._root = (
            workspace_root
            if workspace_root is not None
            else FlextInfraUtilitiesDiscovery.discover_workspace_root_from_file(
                Path(__file__)
            )
        )
        self._package_alias_cache: MutableMapping[str, t.Infra.LazyImportMap] = {}
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
        """Inherit public aliases from the parent package surface."""
        current_pkg = FlextInfraUtilitiesDiscovery.discover_package_from_file(
            pkg_dir / c.Infra.Files.INIT_PY
        )
        if not FlextInfraUtilitiesCodegenGeneration.is_root_namespace_package(
            current_pkg
        ):
            return
        for parent_pkg in FlextInfraUtilitiesDiscovery.resolve_parent_constants_mro(
            pkg_dir,
            return_module=True,
        ):
            parent_dir = self._find_package_directory(pkg_dir, parent_pkg)
            if parent_dir is None or parent_dir.resolve() == pkg_dir.resolve():
                continue
            for alias_name, target in self._collect_package_aliases(
                parent_dir,
                surface=FlextInfraUtilitiesCodegenNamespace.surface_name(current_pkg),
                seen=frozenset(),
            ).items():
                lazy_map.setdefault(alias_name, target)

    def _collect_package_aliases(
        self,
        pkg_dir: Path,
        *,
        surface: str,
        seen: frozenset[str],
    ) -> t.Infra.LazyImportMap:
        package_key = f"{pkg_dir.resolve()}::{surface}"
        cached = self._package_alias_cache.get(package_key)
        if cached is not None:
            return cached
        if package_key in seen:
            return {}
        current_pkg = FlextInfraUtilitiesDiscovery.discover_package_from_file(
            pkg_dir / c.Infra.Files.INIT_PY
        )
        if not current_pkg:
            self._package_alias_cache[package_key] = {}
            return {}
        exports = FlextInfraUtilitiesCodegenLazyScanning.build_sibling_export_index(
            pkg_dir,
            current_pkg,
        )
        child_exports: MutableMapping[str, t.Infra.LazyImportMap] = {}
        for subdir in sorted(pkg_dir.iterdir()):
            if not subdir.is_dir() or subdir.name.startswith("."):
                continue
            if not (subdir / c.Infra.Files.INIT_PY).is_file():
                continue
            child_aliases = self._collect_package_aliases(
                subdir,
                surface=surface,
                seen=seen | {package_key},
            )
            if child_aliases:
                child_exports[str(subdir)] = child_aliases
        if child_exports:
            FlextInfraUtilitiesCodegenLazyMerging.merge_child_exports(
                pkg_dir,
                exports,
                child_exports,
            )
        for parent_pkg in FlextInfraUtilitiesDiscovery.resolve_parent_constants_mro(
            pkg_dir,
            return_module=True,
        ):
            parent_dir = self._find_package_directory(pkg_dir, parent_pkg)
            if parent_dir is None or parent_dir.resolve() == pkg_dir.resolve():
                continue
            for alias_name, target in self._collect_package_aliases(
                parent_dir,
                surface=surface,
                seen=seen | {package_key},
            ).items():
                exports.setdefault(alias_name, target)
        allowed_exports = (
            FlextInfraUtilitiesCodegenNamespace.inherited_exports_for_package(
                surface,
            )
        )
        resolved_aliases = {
            export_name: target
            for export_name, target in exports.items()
            if export_name in allowed_exports
        }
        self._package_alias_cache[package_key] = resolved_aliases
        return resolved_aliases

    def _find_package_directory(self, pkg_dir: Path, package_name: str) -> Path | None:
        project_root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(
            pkg_dir,
        )
        cache_key = (str(project_root) if project_root else "", package_name)
        if cache_key in self._package_dir_cache:
            return self._package_dir_cache[cache_key]
        resolved = next(
            (
                candidate
                for candidate in self._package_candidates(
                    package_name,
                    project_root=project_root,
                )
                if candidate.is_dir()
            ),
            None,
        )
        self._package_dir_cache[cache_key] = resolved
        return resolved

    def _package_candidates(
        self,
        package_name: str,
        *,
        project_root: Path | None,
    ) -> Sequence[Path]:
        package_path = Path(*package_name.split("."))
        root_segment = package_path.parts[0] if package_path.parts else ""
        relative_roots = (
            (Path(),)
            if root_segment in c.Infra.ROOT_WRAPPER_SEGMENTS
            else (
                Path(c.Infra.Paths.DEFAULT_SRC_DIR),
                Path(c.Infra.Directories.DOCS),
                Path(c.Infra.Directories.TESTS),
                Path(c.Infra.Directories.EXAMPLES),
                Path(c.Infra.Directories.SCRIPTS),
            )
        )
        candidates: MutableSequence[Path] = []
        seen: set[Path] = set()
        search_roots = tuple(
            dict.fromkeys(
                root
                for root in (
                    project_root,
                    self._root,
                    *sorted(path for path in self._root.iterdir() if path.is_dir()),
                )
                if root is not None and root.is_dir()
            ),
        )
        for base_dir in search_roots:
            for relative_root in relative_roots:
                candidate = base_dir / relative_root / package_path
                resolved = candidate.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                candidates.append(candidate)
        return tuple(candidates)


__all__ = [
    "FlextInfraUtilitiesCodegenLazyAliases",
    "FlextInfraUtilitiesCodegenLazyMerging",
    "FlextInfraUtilitiesCodegenLazyScanning",
]
