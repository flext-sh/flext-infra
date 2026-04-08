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
    FlextInfraUtilitiesRopeHelpers,
    c,
    t,
)

# =====================================================================
# Merging — child/descendant collection, export merging
# =====================================================================


class FlextInfraUtilitiesCodegenLazyMerging:
    """Child/descendant package collection and export merging helpers."""

    @staticmethod
    def _format_export_target(target: t.Infra.StrPair) -> str:
        """Render one lazy-export target for collision diagnostics."""
        module_path, attr_name = target
        return f"{module_path}.{attr_name}" if attr_name else module_path

    @classmethod
    def register_export(
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
        msg = (
            f"export collision for {name!r}: "
            f"{cls._format_export_target(existing)} != "
            f"{cls._format_export_target(target)}"
        )
        raise ValueError(
            msg,
        )

    @staticmethod
    def should_bubble_up(name: str) -> bool:
        """Check if an export should bubble up to the parent package."""
        if name.startswith("_") or name in {c.Infra.Dunders.INIT, "main"}:
            return False
        if name in c.Infra.ALIAS_NAMES:
            return False
        if name in c.Infra.INFRA_ONLY_EXPORTS:
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
            if FlextInfraUtilitiesCodegenLazyMerging.should_bubble_up(name):
                FlextInfraUtilitiesCodegenLazyMerging.register_export(
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

    _DOCSTRING_RE: t.Infra.RegexPattern = re.compile(
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
        mod_path = FlextInfraUtilitiesCodegenLazyScanning._module_path_from_rel_path(
            rel_path=rel_path,
            current_pkg=current_pkg,
            is_project_root=(pkg_dir / c.Infra.Files.PYPROJECT_FILENAME).exists(),
        )
        if not mod_path:
            return
        try:
            source = py_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except OSError:
            FlextInfraUtilitiesReporting.warning(
                f"skipping {py_file.name}: read failed",
            )
            return
        FlextInfraUtilitiesCodegenLazyScanning._validate_namespace_source(
            source=source,
            py_file=py_file,
            rel_path=rel_path,
            current_pkg=current_pkg,
        )

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

        should_export_symbols = (
            FlextInfraUtilitiesCodegenLazyScanning._should_export_module_symbols(
                mod_path=mod_path,
                py_file=py_file,
            )
        )

        if has_all and should_export_symbols:
            if not FlextInfraUtilitiesCodegenLazyScanning._is_test_fixture_namespace(
                current_pkg,
            ):
                for name in all_exports:
                    if name in c.Infra.INFRA_ONLY_EXPORTS or name == "main":
                        continue
                    FlextInfraUtilitiesCodegenLazyScanning.register_export(
                        index,
                        name,
                        (mod_path, name),
                    )
        elif (
            should_export_symbols
            and not FlextInfraUtilitiesCodegenLazyScanning._is_test_fixture_namespace(
                current_pkg,
            )
        ):
            FlextInfraUtilitiesCodegenLazyScanning._scan_public_defs(
                source,
                mod_path,
                index,
            )

    @staticmethod
    def _should_skip_private_module(
        *,
        py_file: Path,
        current_pkg: str,
    ) -> bool:
        """Skip private underscore modules only at the root namespace layer."""
        if not py_file.stem.startswith("_"):
            return False
        if py_file.name in {
            c.Infra.Files.INIT_PY,
            "__main__.py",
            "__version__.py",
        }:
            return False
        if any(
            part in c.Infra.FAMILY_DIRECTORIES.values()
            for part in current_pkg.split(".")
        ):
            return False
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
    def _is_test_fixture_namespace(current_pkg: str) -> bool:
        return current_pkg.startswith("tests.fixtures")

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
        if is_project_root and root_segment in c.Infra.ROOT_WRAPPER_SEGMENTS:
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
    def _should_export_module_symbols(
        *,
        mod_path: str,
        py_file: Path,
    ) -> bool:
        parts = tuple(part for part in mod_path.split(".") if part)
        if not parts:
            return True
        if parts[0] not in {
            c.Infra.Directories.TESTS,
            c.Infra.Directories.EXAMPLES,
            c.Infra.Directories.SCRIPTS,
        }:
            return True
        if any(part in c.Infra.FAMILY_DIRECTORIES.values() for part in parts):
            return True
        if "services" in parts:
            return True
        return FlextInfraUtilitiesCodegenNamespace.is_root_namespace_file(py_file.name)

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
        if is_project_root and root_segment in c.Infra.ROOT_WRAPPER_SEGMENTS:
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
                if FlextInfraUtilitiesCodegenLazyScanning._skip_test_only_node(
                    node,
                    mod_path=mod_path,
                ):
                    continue
                names.append(node.name)
                continue
            if isinstance(node, ast.Assign):
                if (
                    isinstance(node.value, ast.Call)
                    and FlextInfraUtilitiesCodegenLazyScanning._call_name(
                        node.value.func,
                    )
                    in c.Infra.TYPEVAR_CALLABLES
                ):
                    continue
                names.extend(
                    target.id for target in node.targets if isinstance(target, ast.Name)
                )
                continue
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names.append(node.target.id)

        for name in names:
            if mod_path.startswith("tests.") and name == "pytestmark":
                continue
            if (
                name.startswith("_")
                or name == "main"
                or name in c.Infra.INFRA_ONLY_EXPORTS
            ):
                continue
            FlextInfraUtilitiesCodegenLazyScanning.register_export(
                index,
                name,
                (mod_path, name),
            )

    @staticmethod
    def _validate_namespace_source(
        *,
        source: str,
        py_file: Path,
        rel_path: Path,
        current_pkg: str,
    ) -> None:
        try:
            module = ast.parse(source)
        except SyntaxError:
            return
        FlextInfraUtilitiesCodegenLazyScanning._validate_namespace_contract(
            module=module,
            py_file=py_file,
            rel_path=rel_path,
            current_pkg=current_pkg,
        )

    @classmethod
    def _validate_namespace_contract(
        cls,
        *,
        module: ast.Module,
        py_file: Path,
        rel_path: Path,
        current_pkg: str,
    ) -> None:
        if not FlextInfraUtilitiesCodegenNamespace.should_enforce_geninit_contract(
            rel_path,
            current_pkg=current_pkg,
        ):
            return
        if cls._is_private_fixture_module(py_file):
            cls._validate_fixture_module(module=module, py_file=py_file)
            return
        outer_classes = [node for node in module.body if isinstance(node, ast.ClassDef)]
        if len(outer_classes) != 1:
            count = len(outer_classes)
            msg = (
                f"{py_file}: gen-init requires exactly one outer class (found {count})"
            )
            raise ValueError(
                msg,
            )
        class_node = outer_classes[0]
        cls._validate_outer_class_name(class_node=class_node, py_file=py_file)
        expected_alias = FlextInfraUtilitiesCodegenNamespace.geninit_expected_alias(
            py_file,
        )
        for node in module.body:
            if isinstance(node, ast.ClassDef):
                continue
            if cls._is_allowed_namespace_module_level(
                node=node,
                py_file=py_file,
                expected_alias=expected_alias,
                outer_class_name=class_node.name,
            ):
                continue
            alias_error = cls._unexpected_alias_error(
                node=node,
                py_file=py_file,
                expected_alias=expected_alias,
            )
            if alias_error:
                raise ValueError(alias_error)
            lineno = getattr(node, "lineno", 1)
            statement_name = cls._describe_top_level_statement(node)
            msg = (
                f"{py_file}:{lineno}: disallowed top-level {statement_name}; "
                "move it into the single namespace class"
            )
            raise ValueError(
                msg,
            )

    @classmethod
    def _validate_fixture_module(
        cls,
        *,
        module: ast.Module,
        py_file: Path,
    ) -> None:
        for node in module.body:
            if cls._is_allowed_fixture_module_level(node=node, py_file=py_file):
                continue
            lineno = getattr(node, "lineno", 1)
            statement_name = cls._describe_top_level_statement(node)
            msg = (
                f"{py_file}:{lineno}: disallowed top-level {statement_name}; "
                "fixture modules may only define imports, typevars, and pytest fixtures"
            )
            raise ValueError(msg)

    @staticmethod
    def _is_private_fixture_module(py_file: Path) -> bool:
        return py_file.parent.name == "_fixtures"

    @classmethod
    def _is_allowed_fixture_module_level(
        cls,
        *,
        node: ast.stmt,
        py_file: Path,
    ) -> bool:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return True
        if cls._is_module_docstring(node):
            return True
        if isinstance(node, ast.Assign):
            return cls._is_allowed_namespace_assign(
                node=node,
                py_file=py_file,
                expected_alias=None,
                outer_class_name=None,
            )
        if isinstance(node, ast.AnnAssign):
            return cls._is_allowed_namespace_ann_assign(node=node, py_file=py_file)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cls._is_pytest_fixture(node)
        return False

    @classmethod
    def _validate_outer_class_name(
        cls,
        *,
        class_node: ast.ClassDef,
        py_file: Path,
    ) -> None:
        class_name = class_node.name
        prefix = FlextInfraUtilitiesCodegenNamespace.derive_project_prefix(py_file)
        family = FlextInfraUtilitiesCodegenNamespace.geninit_expected_family(py_file)
        if prefix and not class_name.startswith(prefix):
            msg = (
                f"{py_file}:{class_node.lineno}: class {class_name!r} must start "
                f"with {prefix!r}"
            )
            raise ValueError(
                msg,
            )
        if not family:
            return
        if py_file.parent.name in c.Infra.FAMILY_DIRECTORIES.values():
            family_tokens = (
                FlextInfraUtilitiesCodegenNamespace.geninit_expected_family_tokens(
                    py_file,
                )
            )
            relative_name = class_name[len(prefix) :] if prefix else class_name
            if not any(token in relative_name for token in family_tokens):
                msg = (
                    f"{py_file}:{class_node.lineno}: class {class_name!r} must "
                    f"contain one of {family_tokens!r} after prefix {prefix!r}"
                )
                raise ValueError(
                    msg,
                )
            return
        accepted_suffixes = (
            ("Service", "Services")
            if py_file.name == "service.py" and family == "Service"
            else (family,)
        )
        if not any(class_name.endswith(suffix) for suffix in accepted_suffixes):
            msg = (
                f"{py_file}:{class_node.lineno}: class {class_name!r} must end "
                f"with one of {accepted_suffixes!r}"
            )
            raise ValueError(
                msg,
            )

    @classmethod
    def _is_allowed_namespace_module_level(
        cls,
        *,
        node: ast.stmt,
        py_file: Path,
        expected_alias: str | None,
        outer_class_name: str | None,
    ) -> bool:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return True
        if cls._is_module_docstring(node):
            return True
        if cls._is_allowed_root_cli_main(node=node, py_file=py_file):
            return True
        if cls._is_allowed_root_cli_main_guard(node=node, py_file=py_file):
            return True
        if cls._is_type_checking_block(node=node, py_file=py_file):
            return True
        if isinstance(node, ast.Assign):
            return cls._is_allowed_namespace_assign(
                node=node,
                py_file=py_file,
                expected_alias=expected_alias,
                outer_class_name=outer_class_name,
            )
        if isinstance(node, ast.AnnAssign):
            return cls._is_allowed_namespace_ann_assign(node=node, py_file=py_file)
        if isinstance(node, ast.TypeAlias):
            return cls._is_typings_namespace(py_file)
        return False

    @staticmethod
    def _is_module_docstring(node: ast.stmt) -> bool:
        return (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )

    @staticmethod
    def _is_root_cli_module(py_file: Path) -> bool:
        return py_file.name == "cli.py"

    @classmethod
    def _is_allowed_root_cli_main(
        cls,
        *,
        node: ast.stmt,
        py_file: Path,
    ) -> bool:
        return (
            cls._is_root_cli_module(py_file)
            and isinstance(node, ast.FunctionDef)
            and node.name == "main"
        )

    @classmethod
    def _is_allowed_root_cli_main_guard(
        cls,
        *,
        node: ast.stmt,
        py_file: Path,
    ) -> bool:
        if not cls._is_root_cli_module(py_file):
            return False
        if not isinstance(node, ast.If) or node.orelse:
            return False
        if not cls._is_main_guard_test(node.test):
            return False
        return all(cls._is_main_guard_stmt(stmt) for stmt in node.body)

    @staticmethod
    def _is_main_guard_test(test: ast.expr) -> bool:
        if not isinstance(test, ast.Compare) or len(test.ops) != 1:
            return False
        if not isinstance(test.ops[0], ast.Eq) or len(test.comparators) != 1:
            return False
        left = test.left
        right = test.comparators[0]
        return (
            isinstance(left, ast.Name)
            and left.id == "__name__"
            and isinstance(right, ast.Constant)
            and right.value == "__main__"
        )

    @classmethod
    def _is_main_guard_stmt(cls, stmt: ast.stmt) -> bool:
        if isinstance(stmt, ast.Expr):
            return cls._is_main_call(stmt.value)
        if isinstance(stmt, ast.Raise) and stmt.exc is not None:
            return cls._is_main_call(stmt.exc)
        return False

    @classmethod
    def _is_main_call(cls, expr: ast.expr) -> bool:
        if isinstance(expr, ast.Call):
            if isinstance(expr.func, ast.Name) and expr.func.id == "main":
                return True
            if isinstance(expr.func, ast.Name) and expr.func.id == "SystemExit":
                return (
                    len(expr.args) == 1
                    and not expr.keywords
                    and cls._is_main_call(expr.args[0])
                )
            if isinstance(expr.func, ast.Attribute) and expr.func.attr == "exit":
                return (
                    len(expr.args) == 1
                    and not expr.keywords
                    and cls._is_main_call(expr.args[0])
                )
        return False

    @classmethod
    def _is_type_checking_block(
        cls,
        *,
        node: ast.stmt,
        py_file: Path,
    ) -> bool:
        if not isinstance(node, ast.If) or node.orelse:
            return False
        test = node.test
        is_type_checking = isinstance(test, ast.Name) and test.id == "TYPE_CHECKING"
        if not is_type_checking:
            return False
        project_namespace = cls._type_checking_namespace(py_file)
        if not project_namespace:
            return False
        return all(
            cls._is_allowed_type_checking_import(
                node=item,
                project_namespace=project_namespace,
            )
            for item in node.body
        )

    @staticmethod
    def _type_checking_namespace(py_file: Path) -> str:
        module_path = FlextInfraUtilitiesDiscovery.discover_package_from_file(py_file)
        if not module_path:
            return ""
        return module_path.split(".", 1)[0]

    @staticmethod
    def _is_allowed_type_checking_import(
        *,
        node: ast.stmt,
        project_namespace: str,
    ) -> bool:
        if not isinstance(node, ast.ImportFrom):
            return False
        if node.level != 0 or node.module != project_namespace:
            return False
        if not node.names:
            return False
        allowed_aliases = {"c", "m", "t", "p", "u"}
        return all(
            imported.asname is None and imported.name in allowed_aliases
            for imported in node.names
        )

    @classmethod
    def _is_allowed_namespace_assign(
        cls,
        *,
        node: ast.Assign,
        py_file: Path,
        expected_alias: str | None,
        outer_class_name: str | None,
    ) -> bool:
        target_names = [
            target.id for target in node.targets if isinstance(target, ast.Name)
        ]
        if not target_names:
            return False
        if all(name in c.Infra.DUNDER_ALLOWED for name in target_names):
            return True
        if (
            expected_alias is not None
            and target_names == [expected_alias]
            and isinstance(node.value, (ast.Name, ast.Attribute))
        ):
            return True
        if cls._is_allowed_base_service_alias(
            target_names=target_names,
            value=node.value,
            py_file=py_file,
            outer_class_name=outer_class_name,
        ):
            return True
        singleton_alias = (
            FlextInfraUtilitiesCodegenNamespace.geninit_expected_api_singleton_alias(
                py_file,
            )
        )
        if (
            singleton_alias is not None
            and outer_class_name is not None
            and target_names == [singleton_alias]
            and cls._is_allowed_api_singleton_assign(
                node.value,
                outer_class_name=outer_class_name,
            )
        ):
            return True
        if not isinstance(node.value, ast.Call):
            return False
        func_name = cls._call_name(node.value.func)
        return func_name in c.Infra.TYPEVAR_CALLABLES

    @staticmethod
    def _is_allowed_base_service_alias(
        *,
        target_names: Sequence[str],
        value: ast.expr,
        py_file: Path,
        outer_class_name: str | None,
    ) -> bool:
        if py_file.name != "base.py" or target_names != ["s"]:
            return False
        if outer_class_name is None or not outer_class_name.endswith("ServiceBase"):
            return False
        return isinstance(value, ast.Name) and value.id == outer_class_name

    @staticmethod
    def _is_allowed_api_singleton_assign(
        value: ast.expr,
        *,
        outer_class_name: str,
    ) -> bool:
        if not isinstance(value, ast.Call) or value.args or value.keywords:
            return False
        if not isinstance(value.func, ast.Attribute):
            return False
        return (
            value.func.attr == "get_instance"
            and isinstance(value.func.value, ast.Name)
            and value.func.value.id == outer_class_name
        )

    @classmethod
    def _is_allowed_namespace_ann_assign(
        cls,
        *,
        node: ast.AnnAssign,
        py_file: Path,
    ) -> bool:
        if cls._annotation_contains(node.annotation, "TypeAlias"):
            return cls._is_typings_namespace(py_file)
        return False

    @staticmethod
    def _is_typings_namespace(py_file: Path) -> bool:
        return (
            py_file.name == c.Infra.Files.TYPINGS_PY
            or py_file.parent.name == "_typings"
        )

    @staticmethod
    def _annotation_contains(annotation: ast.expr | None, name: str) -> bool:
        if annotation is None:
            return False
        if isinstance(annotation, ast.Name):
            return annotation.id == name
        if isinstance(annotation, ast.Attribute):
            return annotation.attr == name
        if isinstance(annotation, ast.Subscript):
            return FlextInfraUtilitiesCodegenLazyScanning._annotation_contains(
                annotation.value,
                name,
            )
        return False

    @staticmethod
    def _call_name(func: ast.expr) -> str:
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return ""

    @staticmethod
    def _describe_top_level_statement(node: ast.stmt) -> str:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return f"function {node.name!r}"
        if isinstance(node, ast.Assign):
            names = [
                target.id for target in node.targets if isinstance(target, ast.Name)
            ]
            if names:
                return f"assignment {', '.join(repr(name) for name in names)}"
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            return f"assignment {node.target.id!r}"
        return type(node).__name__

    @staticmethod
    def _unexpected_alias_error(
        *,
        node: ast.stmt,
        py_file: Path,
        expected_alias: str | None,
    ) -> str:
        if not isinstance(node, ast.Assign):
            return ""
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if len(names) != 1:
            return ""
        alias = names[0]
        if alias not in c.Infra.ALIAS_NAMES:
            return ""
        if expected_alias == alias:
            return ""
        if expected_alias is None:
            return (
                f"{py_file}:{node.lineno}: canonical alias {alias!r} is not allowed "
                "in this module"
            )
        return (
            f"{py_file}:{node.lineno}: canonical alias for {py_file.name} must be "
            f"{expected_alias!r}, found {alias!r}"
        )

    @staticmethod
    def _skip_test_only_node(
        node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
        *,
        mod_path: str,
    ) -> bool:
        """Skip pytest-local symbols that must never become package exports."""
        if mod_path.startswith("tests.") and node.name.startswith(
            ("Test", "test_", "main"),
        ):
            return True
        if isinstance(node, ast.ClassDef):
            return False
        return FlextInfraUtilitiesCodegenLazyScanning._is_pytest_fixture(node)

    @staticmethod
    def _is_pytest_fixture(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Return True when a function is decorated as a pytest fixture."""
        for decorator in node.decorator_list:
            target = decorator.func if isinstance(decorator, ast.Call) else decorator
            if isinstance(target, ast.Name) and target.id == "fixture":
                return True
            if isinstance(target, ast.Attribute) and target.attr == "fixture":
                return True
        return False


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
        if not FlextInfraUtilitiesCodegenGeneration.is_root_namespace_package(
            current_pkg
        ):
            return
        for alias, suffix in c.Infra.ALIAS_TO_SUFFIX.items():
            expected_module = "typings" if suffix == "Types" else suffix.lower()
            if self._existing_alias_is_canonical(
                lazy_map, alias, suffix, expected_module
            ):
                continue
            if (
                current_pkg == c.Infra.Packages.CORE_UNDERSCORE
                and alias in c.Infra.CORE_RUNTIME_ALIAS_TARGETS
            ):
                lazy_map[alias] = c.Infra.CORE_RUNTIME_ALIAS_TARGETS[alias]
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
            if alias in c.Infra.CORE_RUNTIME_ALIAS_TARGETS:
                lazy_map[alias] = c.Infra.CORE_RUNTIME_ALIAS_TARGETS[alias]
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
            ("service", ("Service", "Services")),
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
        if root_segment in c.Infra.ROOT_WRAPPER_SEGMENTS:
            candidates.append(base_dir / package_path)
        candidates.append(base_dir / c.Infra.Paths.DEFAULT_SRC_DIR / package_path)
        if root_segment not in c.Infra.ROOT_WRAPPER_SEGMENTS:
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
        if root_segment in c.Infra.ROOT_WRAPPER_SEGMENTS:
            patterns.append(str(Path("*") / package_path))
        else:
            patterns.append(
                str(Path("*") / c.Infra.Paths.DEFAULT_SRC_DIR / package_path)
            )
        if root_segment not in c.Infra.ROOT_WRAPPER_SEGMENTS:
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
