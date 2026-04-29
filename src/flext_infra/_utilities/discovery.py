"""Project discovery utilities for package and workspace resolution."""

from __future__ import annotations

import ast
from collections.abc import (
    Mapping,
    Sequence,
)
from functools import cache
from pathlib import Path
from typing import ClassVar

from flext_infra import FlextInfraUtilitiesDocsScope, c, p, r, t


class FlextInfraUtilitiesDiscovery:
    """Canonical discovery helpers for path, package, and Rope-backed scans."""

    _PARENT_CONSTANTS_MRO_CACHE: ClassVar[dict[tuple[str, bool], tuple[str, ...]]] = {}

    @classmethod
    def _ast_base_candidates(cls, base_node: ast.expr) -> tuple[str, ...]:
        """Return candidate base tokens that can match declared imports."""
        match base_node:
            case ast.Name(id=name):
                return (name,)
            case ast.Attribute(value=value, attr=attr):
                parent_candidates = cls._ast_base_candidates(value)
                chained = tuple(
                    f"{candidate}.{attr}"
                    for candidate in parent_candidates
                    if candidate
                )
                return tuple(dict.fromkeys((*chained, *parent_candidates, attr)))
            case ast.Subscript(value=value):
                return cls._ast_base_candidates(value)
            case _:
                return ()

    @staticmethod
    def _declared_imports_ast(syntax_tree: ast.Module) -> dict[str, str]:
        """Map imported names and aliases declared in one module AST."""
        declared_imports_ast: dict[str, str] = {
            (
                imported_name.asname or imported_name.name
            ): f"{node.module}.{imported_name.name}"
            for node in syntax_tree.body
            if isinstance(node, ast.ImportFrom) and node.module
            for imported_name in node.names
            if imported_name.name != "*"
        }
        declared_imports_ast.update({
            (
                imported_name.asname
                or imported_name.name.split(
                    ".",
                    maxsplit=1,
                )[0]
            ): imported_name.name
            for node in syntax_tree.body
            if isinstance(node, ast.Import)
            for imported_name in node.names
        })
        return declared_imports_ast

    @staticmethod
    def _resolve_imported_base_target(
        base_candidates: tuple[str, ...],
        declared_imports_ast: Mapping[str, str],
    ) -> str:
        """Return the imported target path matching one base candidate set."""
        return next(
            (
                imported_path
                for base_name in base_candidates
                for imported_path in (
                    declared_imports_ast.get(base_name, ""),
                    declared_imports_ast.get(
                        base_name.split(".", maxsplit=1)[0],
                        "",
                    ),
                )
                if imported_path
            ),
            "",
        )

    @staticmethod
    def _resolved_parent_constants_targets(
        discovered_classes: Sequence[ast.ClassDef],
        declared_imports_ast: Mapping[str, str],
        *,
        current_root: str,
        return_module: bool,
    ) -> tuple[str, ...]:
        """Resolve unique imported parent constant targets from discovered classes."""
        resolved: list[str] = []
        resolved_seen: set[str] = set()
        for class_node in discovered_classes:
            for base_candidates in (
                candidates
                for base_node in class_node.bases
                if (
                    candidates := FlextInfraUtilitiesDiscovery._ast_base_candidates(
                        base_node,
                    )
                )
            ):
                target_name = (
                    FlextInfraUtilitiesDiscovery._resolve_imported_base_target(
                        base_candidates,
                        declared_imports_ast,
                    )
                )
                if not target_name:
                    continue
                package_root = target_name.split(".", maxsplit=1)[0]
                target = (
                    package_root
                    if return_module
                    else target_name.rsplit(".", maxsplit=1)[-1]
                )
                if (
                    not target
                    or package_root == current_root
                    or target in resolved_seen
                ):
                    continue
                resolved_seen.add(target)
                resolved.append(target)
        return tuple(resolved)

    @staticmethod
    @cache
    def _discover_project_root_from_path(file_path: str) -> str:
        """Discover the enclosing project root path cached by file path."""
        resolved = Path(file_path).resolve()
        candidate = (
            resolved.parent if resolved.suffix == c.Infra.EXT_PYTHON else resolved
        )
        wrapper_root: Path | None = None
        for current in (candidate, *candidate.parents):
            if current.name == c.Infra.DEFAULT_SRC_DIR:
                wrapper_root = current.parent
                continue
            if current.name in c.Infra.ROOT_WRAPPER_SEGMENTS:
                wrapper_root = current.parent
                continue
            if (current / c.Infra.DEFAULT_SRC_DIR).is_dir():
                return str(current)
        return str(wrapper_root) if wrapper_root is not None else ""

    @staticmethod
    def _relative_path_parts(
        resolved: Path,
        project_root: Path | None,
    ) -> tuple[str, ...]:
        """Return path parts relative to project root when possible."""
        if project_root is None:
            return ()
        try:
            return resolved.relative_to(project_root).parts
        except ValueError:
            return ()

    @staticmethod
    def _normalized_python_parts(
        resolved: Path,
        path_parts: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Normalize file-system parts into package/module parts."""
        if path_parts and path_parts[-1] == c.Infra.INIT_PY:
            return path_parts[:-1]
        if resolved.suffix == c.Infra.EXT_PYTHON and path_parts:
            return path_parts[:-1] + (resolved.stem,)
        return path_parts

    @staticmethod
    def _package_name_from_wrapper_parts(path_parts: tuple[str, ...]) -> str:
        """Return package name when path parts start with a known wrapper."""
        if not path_parts:
            return ""
        root_name = path_parts[0]
        if root_name not in c.Infra.ROOT_WRAPPER_SEGMENTS:
            return ""
        package_parts = (
            path_parts[1:] if root_name == c.Infra.DEFAULT_SRC_DIR else path_parts
        )
        return ".".join(package_parts)

    @staticmethod
    def _package_name_from_src_dir(resolved: Path) -> str:
        """Return the package name when the path is a project root with src/<pkg>."""
        src_dir = resolved / c.Infra.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return ""
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / c.Infra.INIT_PY).is_file():
                return child.name
        return ""

    @staticmethod
    def project_root(file_path: Path) -> Path | None:
        """Discover the enclosing project root for one file or directory path."""
        project_root = FlextInfraUtilitiesDiscovery._discover_project_root_from_path(
            str(file_path),
        )
        return Path(project_root) if project_root else None

    @staticmethod
    @cache
    def _discover_package_from_path(file_path: str) -> str:
        """Discover the package path cached by file path."""
        resolved = Path(file_path).resolve()
        project_root_value = (
            FlextInfraUtilitiesDiscovery._discover_project_root_from_path(file_path)
        )
        project_root = Path(project_root_value) if project_root_value else None
        normalized_parts = FlextInfraUtilitiesDiscovery._normalized_python_parts(
            resolved,
            FlextInfraUtilitiesDiscovery._relative_path_parts(
                resolved,
                project_root,
            ),
        )
        package_name = FlextInfraUtilitiesDiscovery._package_name_from_wrapper_parts(
            normalized_parts,
        )
        if package_name:
            return package_name
        package_name = FlextInfraUtilitiesDiscovery._package_name_from_src_dir(resolved)
        if package_name:
            return package_name
        absolute_parts = FlextInfraUtilitiesDiscovery._normalized_python_parts(
            resolved,
            resolved.parts,
        )
        for index, part in enumerate(absolute_parts):
            package_name = (
                FlextInfraUtilitiesDiscovery._package_name_from_wrapper_parts(
                    absolute_parts[index:],
                )
            )
            if package_name and part in c.Infra.ROOT_WRAPPER_SEGMENTS:
                return package_name
        if resolved.name == c.Infra.INIT_PY:
            top_level_parts = tuple(
                part for part in absolute_parts if part and part != resolved.anchor
            )
            match top_level_parts:
                case (_, package_name):
                    return package_name
                case _:
                    pass
        return (
            FlextInfraUtilitiesDocsScope.project_package_name(project_root)
            if project_root is not None
            else ""
        )

    @staticmethod
    def package_name(file_path: Path) -> str:
        """Discover the module or package path for one Python file or package directory."""
        return FlextInfraUtilitiesDiscovery._discover_package_from_path(str(file_path))

    @staticmethod
    def discover_python_dirs(
        project_dir: Path,
        *,
        skip_dirs: frozenset[str] | None = None,
    ) -> t.StrSequence:
        """Return top-level directories that contain at least one Python file."""
        if not project_dir.is_dir():
            return list[str]()
        effective_skip = skip_dirs if skip_dirs is not None else c.Infra.SKIP_DIRS
        return [
            subdir.name
            for subdir in sorted(project_dir.iterdir())
            if subdir.is_dir()
            and not subdir.name.startswith(".")
            and subdir.name not in effective_skip
            and any(subdir.rglob(c.Infra.EXT_PYTHON_GLOB))
        ]

    @staticmethod
    def package_init_path(workspace_root: Path, package_name: str) -> Path | None:
        """Resolve the public package ``__init__.py`` within a project or workspace."""
        package_parts = Path(*package_name.split("."))
        project_dir = package_name.split(".", maxsplit=1)[0].replace("_", "-")
        candidates = (
            workspace_root / c.Infra.DEFAULT_SRC_DIR / package_parts / c.Infra.INIT_PY,
            workspace_root
            / project_dir
            / c.Infra.DEFAULT_SRC_DIR
            / package_parts
            / c.Infra.INIT_PY,
            workspace_root.parent
            / project_dir
            / c.Infra.DEFAULT_SRC_DIR
            / package_parts
            / c.Infra.INIT_PY,
        )
        for candidate in candidates:
            if candidate.is_file():
                return Path(candidate)
        return None

    @staticmethod
    def package_export_names(
        workspace_root: Path,
        package_name: str,
    ) -> frozenset[str]:
        """Return literal ``__all__`` names for a resolved public package."""
        init_path = FlextInfraUtilitiesDiscovery.package_init_path(
            workspace_root,
            package_name,
        )
        if init_path is None:
            return frozenset()
        try:
            module = ast.parse(init_path.read_text(encoding=c.Cli.ENCODING_DEFAULT))
        except (OSError, SyntaxError):
            return frozenset()
        for node in module.body:
            if not isinstance(node, ast.Assign):
                continue
            if not any(
                isinstance(target, ast.Name) and target.id == c.Infra.DUNDER_ALL
                for target in node.targets
            ):
                continue
            try:
                value = ast.literal_eval(node.value)
            except (TypeError, ValueError, SyntaxError):
                return frozenset()
            if isinstance(value, (list, tuple)):
                return frozenset(item for item in value if isinstance(item, str))
        return frozenset()

    @staticmethod
    def package_source_priority(package_names: t.StrSequence) -> t.StrSequence:
        """Return package sources ordered so later duplicates keep priority."""
        ordered: list[str] = []
        for package_name in package_names:
            if not package_name:
                continue
            if package_name in ordered:
                ordered.remove(package_name)
            ordered.append(package_name)
        return tuple(ordered)

    @staticmethod
    def _sibling_project_roots(project_root: Path) -> tuple[Path, ...]:
        parent = project_root.parent
        if not parent.is_dir():
            return ()
        return tuple(
            child
            for child in parent.iterdir()
            if child != project_root
            and child.is_dir()
            and (child / c.Infra.DEFAULT_SRC_DIR).is_dir()
            and (
                (child / c.Infra.PYPROJECT_FILENAME).is_file()
                or (child / c.Infra.GO_MOD).is_file()
            )
        )

    @staticmethod
    def _child_project_roots(workspace_root: Path) -> tuple[Path, ...]:
        if not workspace_root.is_dir():
            return ()
        return tuple(
            child
            for child in workspace_root.iterdir()
            if child.is_dir()
            and not child.name.startswith(".")
            and any(
                (child / dir_name).is_dir() for dir_name in c.Infra.MRO_SCAN_DIRECTORIES
            )
            and (
                (child / c.Infra.PYPROJECT_FILENAME).is_file()
                or (child / c.Infra.GO_MOD).is_file()
            )
        )

    @staticmethod
    def rope_workspace_root(workspace_root: Path) -> Path:
        """Return the canonical root for a shared Rope project."""
        resolved_root = workspace_root.resolve()
        has_local_scan_dirs = any(
            (resolved_root / dir_name).is_dir()
            for dir_name in c.Infra.MRO_SCAN_DIRECTORIES
        )
        has_project_marker = any(
            candidate.is_file()
            for candidate in (
                resolved_root / c.Infra.PYPROJECT_FILENAME,
                resolved_root / c.Infra.GO_MOD,
                resolved_root / c.Infra.MAKEFILE_FILENAME,
            )
        )
        if has_local_scan_dirs and not has_project_marker:
            return resolved_root
        if FlextInfraUtilitiesDiscovery._child_project_roots(resolved_root):
            return resolved_root
        project_root = (
            FlextInfraUtilitiesDiscovery.project_root(resolved_root) or resolved_root
        )
        if FlextInfraUtilitiesDiscovery._sibling_project_roots(project_root):
            return project_root.parent
        return resolved_root

    @staticmethod
    def find_all_pyproject_files(
        workspace_root: Path,
        *,
        skip_dirs: frozenset[str] | None = None,
        project_paths: Sequence[Path] | None = None,
    ) -> p.Result[Sequence[Path]]:
        """Find all ``pyproject.toml`` files under one workspace root."""
        if not workspace_root.exists():
            return r[Sequence[Path]].ok([])
        effective_skip = skip_dirs if skip_dirs is not None else c.Infra.SKIP_DIRS
        try:
            all_files = [
                path
                for path in workspace_root.rglob(c.Infra.PYPROJECT_FILENAME)
                if not any(
                    part in effective_skip
                    for part in path.relative_to(workspace_root).parts[:-1]
                )
            ]
        except OSError as exc:
            return r[Sequence[Path]].fail(f"pyproject file scan failed: {exc}")
        if project_paths is not None:
            all_files = [
                path
                for path in all_files
                if any(
                    path.is_relative_to(project_path) for project_path in project_paths
                )
            ]
        return r[Sequence[Path]].ok(all_files)

    @classmethod
    def resolve_parent_constants_mro(
        cls,
        pkg_dir_or_file: Path,
        *,
        return_module: bool = False,
    ) -> tuple[str, ...]:
        """Resolve imported parent constants through AST and declared imports."""
        constants_file = (
            pkg_dir_or_file
            if pkg_dir_or_file.name == c.Infra.CONSTANTS_PY
            else pkg_dir_or_file / c.Infra.CONSTANTS_PY
        )
        if not constants_file.is_file():
            return ()
        project_root = FlextInfraUtilitiesDiscovery.project_root(
            constants_file,
        )
        if project_root is None:
            return ()
        current_module = FlextInfraUtilitiesDiscovery.package_name(
            constants_file,
        )
        cache_key = (str(constants_file.resolve()), return_module)
        cached = cls._PARENT_CONSTANTS_MRO_CACHE.get(cache_key)
        if cached is not None:
            return cached
        try:
            syntax_tree = ast.parse(
                constants_file.read_text(encoding=c.Cli.ENCODING_DEFAULT),
            )
        except (OSError, SyntaxError):
            syntax_tree = ast.Module(body=[], type_ignores=[])
        declared_imports_ast = cls._declared_imports_ast(syntax_tree)
        discovered_classes = [
            node
            for node in syntax_tree.body
            if isinstance(node, ast.ClassDef) and "Constants" in node.name
        ]
        current_root = (
            current_module.split(".", maxsplit=1)[0] if current_module else ""
        )
        result = cls._resolved_parent_constants_targets(
            discovered_classes,
            declared_imports_ast,
            current_root=current_root,
            return_module=return_module,
        )
        cls._PARENT_CONSTANTS_MRO_CACHE[cache_key] = result
        return result

    @staticmethod
    def resolve_transitive_parent_packages(
        workspace_root: Path,
        package_names: t.StrSequence,
    ) -> tuple[str, ...]:
        """Resolve parent packages transitively with ancestors ordered before children."""
        resolved: list[str] = []
        visited: set[str] = set()

        def visit(package_name: str) -> None:
            if not package_name or package_name in visited:
                return
            visited.add(package_name)
            init_path = FlextInfraUtilitiesDiscovery.package_init_path(
                workspace_root,
                package_name,
            )
            if init_path is not None:
                for (
                    parent_package
                ) in FlextInfraUtilitiesDiscovery.resolve_parent_constants_mro(
                    init_path.parent,
                    return_module=True,
                ):
                    visit(parent_package)
            resolved.append(package_name)

        for package_name in package_names:
            visit(package_name)
        prioritized = FlextInfraUtilitiesDiscovery.package_source_priority(
            (*resolved, *package_names),
        )
        return tuple(prioritized)

    @staticmethod
    def contextual_runtime_alias_sources(
        *,
        project_root: Path,
        file_path: Path,
    ) -> Mapping[str, frozenset[str]]:
        """Return allowed foreign-package runtime alias sources for one file."""
        package_name = FlextInfraUtilitiesDocsScope.project_package_name(project_root)
        if not package_name:
            return {}
        package_dir = (
            project_root
            / c.Infra.DEFAULT_SRC_DIR
            / Path(
                *package_name.split("."),
            )
        )
        if not (package_dir / c.Infra.INIT_PY).is_file():
            return {}
        parent_packages = FlextInfraUtilitiesDiscovery.resolve_parent_constants_mro(
            package_dir,
            return_module=True,
        )
        if not parent_packages:
            return {}
        allowed_sources = frozenset(
            package.split(".", maxsplit=1)[0] for package in parent_packages
        )
        for family_dir in c.Infra.FAMILY_DIRECTORIES.values():
            if file_path.is_relative_to(package_dir / family_dir):
                return dict.fromkeys(c.Infra.MRO_FAMILIES, allowed_sources)
        return {}


__all__: list[str] = ["FlextInfraUtilitiesDiscovery"]
