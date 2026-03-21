"""Project discovery utilities for workspace scanning."""

from __future__ import annotations

import re
from pathlib import Path

import libcst as cst

from flext_core import r
from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing
from flext_infra.constants import FlextInfraConstants as c
from flext_infra.models import FlextInfraModels as m


class FlextInfraUtilitiesDiscovery:
    """Static project discovery utilities."""

    @staticmethod
    def discover_projects(
        workspace_root: Path,
    ) -> r[list[m.Infra.ProjectInfo]]:
        """Find all FLEXT projects in the workspace."""
        try:
            projects: list[m.Infra.ProjectInfo] = []
            submodules = FlextInfraUtilitiesDiscovery._submodule_names(workspace_root)
            for entry in sorted(workspace_root.iterdir(), key=lambda v: v.name):
                if (
                    not entry.is_dir()
                    or entry.name == "cmd"
                    or entry.name.startswith(".")
                ):
                    continue
                if not (entry / ".git").exists():
                    continue
                if not (entry / "Makefile").exists():
                    continue
                has_pyproject = (entry / "pyproject.toml").exists()
                if not has_pyproject:
                    continue
                kind = "submodule" if entry.name in submodules else "external"
                projects.append(
                    m.Infra.ProjectInfo(
                        path=entry,
                        name=entry.name,
                        stack=f"python/{kind}",
                        has_tests=(entry / "tests").is_dir(),
                        has_src=(entry / "src").is_dir(),
                    ),
                )
            return r[list[m.Infra.ProjectInfo]].ok(projects)
        except OSError as exc:
            return r[list[m.Infra.ProjectInfo]].fail(f"discovery failed: {exc}")

    @staticmethod
    def _submodule_names(workspace_root: Path) -> set[str]:
        gitmodules = workspace_root / ".gitmodules"
        if not gitmodules.exists():
            return set()
        try:
            content = gitmodules.read_text(encoding="utf-8")
        except OSError:
            return set()
        return set(re.findall(r"^\s*path\s*=\s*(.+?)\s*$", content, re.MULTILINE))

    @staticmethod
    def discover_project_root_from_file(file_path: Path) -> Path | None:
        """Discover the project root directory starting from a file path."""
        resolved = file_path.resolve()
        candidate = resolved.parent if resolved.is_file() else resolved
        lineage = (candidate, *candidate.parents)
        for current in lineage:
            if current.name == "src":
                return current.parent
            if (current / "src").is_dir():
                return current
        return None

    @staticmethod
    def discover_package_from_file(file_path: Path) -> str:
        """Discover the package name for a Python file."""
        resolved = file_path.resolve()
        candidate = resolved.parent if resolved.is_file() else resolved
        lineage = (candidate, *candidate.parents)
        for current in lineage:
            if current.name != "src":
                continue
            try:
                relative = resolved.relative_to(current)
                if relative.parts:
                    package_name = relative.parts[0]
                    if (current / package_name / "__init__.py").is_file():
                        return package_name
            except ValueError:
                continue
        project_root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(
            file_path,
        )
        if project_root is None:
            return ""
        src_dir = project_root / "src"
        if not src_dir.is_dir():
            return ""
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / "__init__.py").is_file():
                return child.name
        return ""

    @staticmethod
    def discover_workspace_root_from_file(file_path: Path) -> Path:
        """Discover the workspace root."""
        root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(file_path)
        return root.parent if root else file_path.resolve().parent

    @staticmethod
    def discover_workspace_packages(workspace_root: Path) -> frozenset[str]:
        """Discover all project package names in the workspace."""
        packages: set[str] = set()
        if not workspace_root.is_dir():
            return frozenset()
        for entry in workspace_root.iterdir():
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            name = FlextInfraUtilitiesDiscovery.discover_package_from_file(
                entry / "src"
            )
            if name:
                packages.add(name)
        return frozenset(packages)

    @staticmethod
    def package_context(file_path: Path) -> tuple[Path, str]:
        """Return (package_dir, package_name) for any project type."""
        parts = file_path.resolve().parts
        # 1. Standard FLEXT structure: .../src/<package_name>/...
        if "src" in parts:
            src_idx = parts.index("src")
            # Package name is always the directory immediately after 'src'
            if src_idx + 1 < len(parts):
                package_name = parts[src_idx + 1]
                package_dir = Path(*parts[: src_idx + 2])
                return package_dir, package_name

        # 2. Alternative structure: find highest-level directory with __init__.py
        current = file_path.resolve().parent
        best_dir, best_name = current, ""
        while current.parent != current:
            if (current / "__init__.py").is_file():
                best_dir, best_name = current, current.name
            elif best_name:  # Stop once we've crossed out of the package
                break
            current = current.parent
        return best_dir, best_name

    @staticmethod
    def discover_core_package(project_root: Path) -> str:
        """Discover the core package name for a project."""
        pyproject = project_root / "pyproject.toml"
        if pyproject.is_file():
            content = pyproject.read_text(encoding="utf-8")
            if "flext-core" in content or "flext_core" in content:
                return "flext_core"
        return "flext_core"

    @staticmethod
    def discover_project_aliases(project_root: Path) -> dict[str, str]:
        """Discover all single-char aliases in a project."""
        src_package = FlextInfraUtilitiesDiscovery.discover_src_package_dir(
            project_root
        )
        if src_package is None:
            return {}
        _package_name, package_dir = src_package
        alias_to_facade: dict[str, str] = {}
        facades = [
            "models.py",
            "utilities.py",
            "constants.py",
            "typings.py",
            "protocols.py",
        ]
        for facade_name in facades:
            facade_path = package_dir / facade_name
            if not facade_path.is_file():
                continue
            alias = FlextInfraUtilitiesDiscovery.extract_declared_alias_from_facade(
                facade_path,
            )
            if len(alias) == 1 and alias.islower():
                alias_to_facade[alias] = facade_name
        return alias_to_facade

    @staticmethod
    def extract_declared_alias_from_facade(file_path: Path) -> str:
        """Extract the single-char alias defined in a facade file."""
        module = FlextInfraUtilitiesParsing.parse_module_cst(file_path)
        if module is None:
            return ""
        for stmt_line in module.body:
            if not isinstance(stmt_line, cst.SimpleStatementLine):
                continue
            for stmt in stmt_line.body:
                if (
                    isinstance(stmt, cst.Assign)
                    and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0].target, cst.Name)
                    and len(stmt.targets[0].target.value) == 1
                    and isinstance(stmt.value, cst.Name)
                ):
                    return stmt.targets[0].target.value
        return ""

    @staticmethod
    def extract_lazy_import_map(init_path: Path) -> dict[str, str]:
        """Extract PEP 562 lazy import map from an __init__.py file."""
        if not init_path.is_file():
            return {}
        module = FlextInfraUtilitiesParsing.parse_module_cst(init_path)
        if module is None:
            return {}
        for stmt_line in module.body:
            if not isinstance(stmt_line, cst.SimpleStatementLine):
                continue
            for stmt in stmt_line.body:
                target = None
                if isinstance(stmt, cst.Assign) and len(stmt.targets) == 1:
                    target = stmt.targets[0].target
                elif isinstance(stmt, cst.AnnAssign):
                    target = stmt.target
                if (
                    isinstance(target, cst.Name)
                    and target.value == "_LAZY_IMPORTS"
                    and isinstance(stmt.value, cst.Dict)
                ):
                    return FlextInfraUtilitiesDiscovery._extract_lazy_aliases(
                        stmt.value,
                    )
        return {}

    @staticmethod
    def _extract_lazy_aliases(value: cst.Dict) -> dict[str, str]:
        result: dict[str, str] = {}
        for element in value.elements:
            if not isinstance(element, cst.DictElement):
                continue
            key = FlextInfraUtilitiesParsing.extract_string_literal(element.key)
            if len(key) != 1 or not key.islower():
                continue
            if (
                not isinstance(element.value, (cst.Tuple, cst.List))
                or not element.value.elements
            ):
                continue
            module_name = FlextInfraUtilitiesParsing.extract_string_literal(
                element.value.elements[0].value
            )
            if module_name:
                result[key] = module_name.split(".")[-1]
        return result

    @staticmethod
    def discover_python_dirs(
        project_dir: Path,
        *,
        skip_dirs: frozenset[str] | None = None,
    ) -> list[str]:
        """Discover all directories containing Python files in a project.

        SSOT discovery function used by all tool config phases
        (pyright, ruff, pyrefly, mypy, extra_paths) and codegen.

        Args:
            project_dir: Project root directory to scan.
            skip_dirs: Directory names to skip. Defaults to c.Infra.SKIP_DIRS.

        Returns:
            Sorted list of directory names that contain at least one .py file.

        """
        if not project_dir.is_dir():
            return []
        effective_skip = skip_dirs if skip_dirs is not None else c.Infra.SKIP_DIRS
        dirs: list[str] = []
        for subdir in sorted(project_dir.iterdir()):
            if not subdir.is_dir():
                continue
            if subdir.name.startswith(".") or subdir.name in effective_skip:
                continue
            has_py = any(subdir.rglob("*.py"))
            if has_py:
                dirs.append(subdir.name)
        return dirs

    @staticmethod
    def discover_src_package_dir(project_root: Path) -> tuple[str, Path] | None:
        """Find the main package directory inside src/."""
        src_dir = project_root / "src"
        if not src_dir.is_dir():
            return None
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / "__init__.py").is_file():
                return child.name, child
        return None

    @staticmethod
    def find_all_pyproject_files(
        workspace_root: Path,
        *,
        skip_dirs: frozenset[str] | None = None,
        project_paths: list[Path] | None = None,
    ) -> r[list[Path]]:
        """Find all pyproject.toml files in the workspace, respecting skip_dirs and project_paths.

        Args:
            workspace_root: Root directory to search
            skip_dirs: Directory names to skip during traversal (defaults to c.Infra.SKIP_DIRS)
            project_paths: If provided, only include files within these paths

        Returns:
            r[list[Path]]: Result with list of pyproject.toml paths, or failure if OSError occurs

        """
        if not workspace_root.exists():
            return r[list[Path]].ok([])
        effective_skip = skip_dirs if skip_dirs is not None else c.Infra.SKIP_DIRS
        try:
            all_files = [
                p
                for p in workspace_root.rglob("pyproject.toml")
                if not any(
                    part in effective_skip
                    for part in p.relative_to(workspace_root).parts[:-1]
                )
            ]
        except OSError as exc:
            return r[list[Path]].fail(f"pyproject file scan failed: {exc}")
        if project_paths is not None:
            all_files = [
                f
                for f in all_files
                if any(f.is_relative_to(pp) for pp in project_paths)
            ]
        return r[list[Path]].ok(all_files)


__all__ = ["FlextInfraUtilitiesDiscovery"]
