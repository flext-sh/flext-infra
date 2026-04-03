"""Project discovery utilities for workspace scanning."""

from __future__ import annotations

import re
from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_core import r
from flext_infra import c, m, t


class FlextInfraUtilitiesDiscovery:
    """Static project discovery utilities."""

    @staticmethod
    def discover_projects(
        workspace_root: Path,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        """Find all FLEXT projects in the workspace."""
        try:
            projects: MutableSequence[m.Infra.ProjectInfo] = []
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
                        has_src=(entry / c.Infra.Paths.DEFAULT_SRC_DIR).is_dir(),
                    ),
                )
            return r[Sequence[m.Infra.ProjectInfo]].ok(projects)
        except OSError as exc:
            return r[Sequence[m.Infra.ProjectInfo]].fail(f"discovery failed: {exc}")

    @staticmethod
    def _submodule_names(workspace_root: Path) -> t.Infra.StrSet:
        gitmodules = workspace_root / ".gitmodules"
        if not gitmodules.exists():
            return set()
        try:
            content = gitmodules.read_text(encoding=c.Infra.Encoding.DEFAULT)
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
            if current.name == c.Infra.Paths.DEFAULT_SRC_DIR:
                return current.parent
            if (current / c.Infra.Paths.DEFAULT_SRC_DIR).is_dir():
                return current
        return None

    @staticmethod
    def discover_package_from_file(file_path: Path) -> str:
        """Discover the package name for a Python file."""
        resolved = file_path.resolve()
        probe_path = FlextInfraUtilitiesDiscovery._package_probe_path(resolved)
        module_path = FlextInfraUtilitiesDiscovery.discover_module_path(probe_path)
        if module_path:
            return module_path
        via_src = FlextInfraUtilitiesDiscovery._discover_package_via_src_lineage(
            resolved,
        )
        if via_src:
            return via_src
        return FlextInfraUtilitiesDiscovery._discover_package_via_project_root(
            file_path,
        )

    @staticmethod
    def _package_probe_path(path: Path) -> Path:
        """Return a synthetic __init__.py path for package-path discovery."""
        if path.suffix == c.Infra.Extensions.PYTHON:
            if path.name == c.Infra.Files.INIT_PY:
                return path
            return path.parent / c.Infra.Files.INIT_PY
        return path / c.Infra.Files.INIT_PY

    @staticmethod
    def _discover_package_via_src_lineage(resolved: Path) -> str:
        """Walk parent directories looking for a src/ boundary with a package."""
        candidate = (
            resolved.parent
            if resolved.suffix == c.Infra.Extensions.PYTHON
            else resolved
        )
        lineage = (candidate, *candidate.parents)
        for current in lineage:
            if current.name != c.Infra.Paths.DEFAULT_SRC_DIR:
                continue
            try:
                relative = resolved.relative_to(current)
                relative_parts = relative.parts
                if relative_parts and relative_parts[-1] == c.Infra.Files.INIT_PY:
                    relative_parts = relative_parts[:-1]
                if not relative_parts:
                    continue
                package_name = ".".join(relative_parts)
                if package_name:
                    return package_name
            except ValueError:
                continue
        return ""

    @staticmethod
    def _discover_package_via_project_root(file_path: Path) -> str:
        """Fallback: find project root and return its first src/ package."""
        project_root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(
            file_path,
        )
        if project_root is None:
            return ""
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return ""
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / c.Infra.Files.INIT_PY).is_file():
                return child.name
        return ""

    @staticmethod
    def discover_module_path(path: Path) -> str:
        """Discover the fully qualified module path for a Python file."""
        root_markers = {
            c.Infra.Directories.EXAMPLES,
            c.Infra.Directories.SCRIPTS,
            c.Infra.Paths.DEFAULT_SRC_DIR,
            c.Infra.Directories.TESTS,
        }
        abs_parts = path.absolute().parts
        for index, part in enumerate(abs_parts):
            if part not in root_markers:
                continue
            pkg_parts = abs_parts[index + 1 : -1]
            if part == c.Infra.Paths.DEFAULT_SRC_DIR:
                return ".".join(pkg_parts)
            return ".".join([part, *pkg_parts]) if pkg_parts else part
        return ""

    @staticmethod
    def discover_workspace_root_from_file(file_path: Path) -> Path:
        """Discover the workspace root."""
        root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(file_path)
        return root.parent if root else file_path.resolve().parent

    @staticmethod
    def discover_workspace_packages(workspace_root: Path) -> frozenset[str]:
        """Discover all project package names in the workspace."""
        packages: t.Infra.StrSet = set()
        if not workspace_root.is_dir():
            return frozenset()
        for entry in workspace_root.iterdir():
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            name = FlextInfraUtilitiesDiscovery.discover_package_from_file(
                entry / c.Infra.Paths.DEFAULT_SRC_DIR,
            )
            if name:
                packages.add(name)
        return frozenset(packages)

    @staticmethod
    def package_context(file_path: Path) -> t.Infra.Pair[Path, str]:
        """Return (package_dir, package_name) for any project type."""
        parts = file_path.resolve().parts
        # 1. Standard FLEXT structure: .../src/<package_name>/...
        if c.Infra.Paths.DEFAULT_SRC_DIR in parts:
            src_idx = parts.index(c.Infra.Paths.DEFAULT_SRC_DIR)
            # Package name is always the directory immediately after 'src'
            if src_idx + 1 < len(parts):
                package_name = parts[src_idx + 1]
                package_dir = Path(*parts[: src_idx + 2])
                return package_dir, package_name

        # 2. Alternative structure: find highest-level directory with __init__.py
        current = file_path.resolve().parent
        best_dir, best_name = current, ""
        while current.parent != current:
            if (current / c.Infra.Files.INIT_PY).is_file():
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
            content = pyproject.read_text(encoding=c.Infra.Encoding.DEFAULT)
            if "flext-core" in content or "flext_core" in content:
                return "flext_core"
        return "flext_core"

    @staticmethod
    def discover_project_aliases(project_root: Path) -> t.StrMapping:
        """Discover all single-char aliases in a project."""
        src_package = FlextInfraUtilitiesDiscovery.discover_src_package_dir(
            project_root,
        )
        if src_package is None:
            return {}
        _package_name, package_dir = src_package
        alias_to_facade: t.MutableStrMapping = {}
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
        if not file_path.is_file():
            return ""
        try:
            content = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            match = re.search(
                r"^\s*([a-z])\s*=\s*[A-Z][a-zA-Z0-9_]+\s*$", content, re.MULTILINE
            )
            return match.group(1) if match else ""
        except OSError:
            return ""

    @staticmethod
    def extract_lazy_import_map(init_path: Path) -> t.StrMapping:
        """Extract PEP 562 lazy import map from an __init__.py file."""
        targets = FlextInfraUtilitiesDiscovery.extract_lazy_import_targets(init_path)
        return {
            alias_name: module_name.split(".")[-1]
            for alias_name, module_name in targets.items()
            if len(alias_name) == 1 and alias_name.islower()
        }

    @staticmethod
    def extract_lazy_import_targets(init_path: Path) -> t.StrMapping:
        """Extract `_LAZY_IMPORTS` targets from an autogenerated package init."""
        if not init_path.is_file():
            return {}
        try:
            content = init_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            targets: t.MutableStrMapping = {}
            dict_match = re.search(
                r"_LAZY_IMPORTS\s*(?::\s*[^=]+)?\s*=\s*(?:merge_lazy_imports\s*\(\s*)?\{([^}]+)\}",
                content,
                re.DOTALL,
            )
            if dict_match:
                for line in dict_match.group(1).splitlines():
                    match = re.search(
                        r"""["']([a-zA-Z0-9_]+)["']\s*:\s*[([]?\s*["']([a-zA-Z0-9_\.]+)["']""",
                        line,
                    )
                    if match:
                        targets[match.group(1)] = match.group(2)
            return targets
        except OSError:
            return {}

    @staticmethod
    def discover_python_dirs(
        project_dir: Path,
        *,
        skip_dirs: frozenset[str] | None = None,
    ) -> t.StrSequence:
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
        return [
            subdir.name
            for subdir in sorted(project_dir.iterdir())
            if subdir.is_dir()
            and not subdir.name.startswith(".")
            and subdir.name not in effective_skip
            and any(subdir.rglob("*.py"))
        ]

    @staticmethod
    def discover_src_package_dir(project_root: Path) -> t.Infra.Pair[str, Path] | None:
        """Find the main package directory inside src/."""
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return None
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / c.Infra.Files.INIT_PY).is_file():
                return child.name, child
        return None

    @staticmethod
    def find_all_pyproject_files(
        workspace_root: Path,
        *,
        skip_dirs: frozenset[str] | None = None,
        project_paths: Sequence[Path] | None = None,
    ) -> r[Sequence[Path]]:
        """Find all pyproject.toml files in the workspace, respecting skip_dirs and project_paths.

        Args:
            workspace_root: Root directory to search
            skip_dirs: Directory names to skip during traversal (defaults to c.Infra.SKIP_DIRS)
            project_paths: If provided, only include files within these paths

        Returns:
            r[Sequence[Path]]: Result with list of pyproject.toml paths, or failure if OSError occurs

        """
        if not workspace_root.exists():
            return r[Sequence[Path]].ok([])
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
            return r[Sequence[Path]].fail(f"pyproject file scan failed: {exc}")
        if project_paths is not None:
            all_files = [
                f
                for f in all_files
                if any(f.is_relative_to(pp) for pp in project_paths)
            ]
        return r[Sequence[Path]].ok(all_files)

    @staticmethod
    def resolve_parent_constants(
        pkg_dir_or_file: Path,
        *,
        return_module: bool = False,
    ) -> str:
        """Find the parent constants class or module from constants.py imports.

        Unified helper replacing 3 near-identical implementations.
        If return_module=True returns the dotted module (e.g. "flext_core").
        Otherwise returns the class name (e.g. "FlextCoreConstants").
        Falls back to "flext_core" (module) or "" (class) if not found.
        """
        constants_file = (
            pkg_dir_or_file
            if pkg_dir_or_file.name == "constants.py"
            else pkg_dir_or_file / "constants.py"
        )
        if not constants_file.is_file():
            return "flext_core" if return_module else ""
        try:
            source = constants_file.read_text(c.Infra.Encoding.DEFAULT)
        except (OSError, UnicodeDecodeError):
            return "flext_core" if return_module else ""
        match = c.Infra.Detection.IMPORT_CONSTANTS_RE.search(source)
        if not match:
            return "flext_core" if return_module else ""
        module = match.group(1)
        class_name = match.group(2)
        if return_module:
            return module
        return class_name

    @staticmethod
    def discover_project_package_name(*, project_root: Path) -> str:
        """Discover the Python package name under ``src/`` for a project root.

        Returns the first package directory name (e.g. ``flext_infra``).
        """
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return ""
        for entry in sorted(src_dir.iterdir(), key=lambda item: item.name):
            if entry.is_dir() and (entry / c.Infra.Files.INIT_PY).is_file():
                return entry.name
        return ""


__all__ = ["FlextInfraUtilitiesDiscovery"]
