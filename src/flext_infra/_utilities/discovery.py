"""Project discovery utilities for package and workspace resolution."""

from __future__ import annotations

from functools import cache
from importlib import util as importlib_util
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from flext_infra import c, m, r, t
from flext_infra._utilities.namespace_config import FlextInfraUtilitiesNamespaceConfig
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery
from flext_infra._utilities.pyproject import FlextInfraUtilitiesPyproject
from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesDiscovery(
    FlextInfraUtilitiesNamespaceConfig,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesPyproject,
    FlextInfraUtilitiesRopeAnalysis,
):
    """Canonical discovery helpers for path, package, and Rope-backed scans."""

    _PARENT_CONSTANTS_MRO_CACHE: ClassVar[dict[tuple[str, bool], t.StrSequence]] = {}

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
    def _relative_path_parts(resolved: Path, project_root: Path | None) -> t.StrTuple:
        """Return path parts relative to project root when possible."""
        if project_root is None:
            return ()
        try:
            return resolved.relative_to(project_root).parts
        except ValueError:
            return ()

    @staticmethod
    def _normalized_python_parts(resolved: Path, path_parts: t.StrTuple) -> t.StrTuple:
        """Normalize filesystem parts into package/module parts."""
        if path_parts and path_parts[-1] == c.Infra.INIT_PY:
            return path_parts[:-1]
        if resolved.suffix == c.Infra.EXT_PYTHON and path_parts:
            return (*path_parts[:-1], resolved.stem)
        return path_parts

    @staticmethod
    def _package_name_from_wrapper_parts(path_parts: t.StrSequence) -> str:
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
                child_path: Path = child
                return child_path.name
        return ""

    @staticmethod
    def project_root(file_path: Path) -> Path | None:
        """Discover the enclosing project root for one file or directory path."""
        project_root = FlextInfraUtilitiesDiscovery._discover_project_root_from_path(
            str(file_path)
        )
        return Path(project_root) if project_root else None

    @classmethod
    @cache
    def _discover_package_from_path(cls, file_path: str) -> str:
        """Discover the package path cached by file path."""
        resolved = Path(file_path).resolve()
        project_root_value = cls._discover_project_root_from_path(file_path)
        project_root = Path(project_root_value) if project_root_value else None
        normalized_parts = cls._normalized_python_parts(
            resolved, cls._relative_path_parts(resolved, project_root)
        )
        package_name = cls._package_name_from_wrapper_parts(normalized_parts)
        if package_name:
            return package_name
        package_name = cls._package_name_from_src_dir(resolved)
        if package_name:
            return package_name
        absolute_parts = cls._normalized_python_parts(resolved, resolved.parts)
        for index, part in enumerate(absolute_parts):
            package_name = cls._package_name_from_wrapper_parts(absolute_parts[index:])
            if package_name and part in c.Infra.ROOT_WRAPPER_SEGMENTS:
                return package_name
        if resolved.name == c.Infra.INIT_PY:
            top_level_parts = tuple(
                part for part in absolute_parts if part and part != resolved.anchor
            )
            match top_level_parts:
                case (_, package_name):
                    resolved_package: str = package_name
                    return resolved_package
                case _:
                    pass
        if project_root is None:
            return ""

        return cls.project_package_name(project_root)

    @classmethod
    def package_name(cls, file_path: Path) -> str:
        """Discover the module or package path for one Python file or package directory."""
        return cls._discover_package_from_path(str(file_path))

    @classmethod
    def alias_migration_context(cls, file_path: Path) -> m.Infra.AliasMigrationContext:
        """Resolve project policy ownership and public import root for one file."""
        project_root = cls.project_root(file_path)
        if project_root is None:
            return m.Infra.AliasMigrationContext(policy_owner="", import_root="")
        policy_owner = cls.project_package_name(project_root)
        try:
            relative_parts = (
                file_path.resolve().relative_to(project_root.resolve()).parts
            )
        except ValueError:
            relative_parts = ()
        import_root = (
            c.Infra.DIR_TESTS
            if relative_parts and relative_parts[0] == c.Infra.DIR_TESTS
            else policy_owner
        )
        return m.Infra.AliasMigrationContext(
            policy_owner=policy_owner, import_root=import_root
        )

    @staticmethod
    def package_importable(package_name: str) -> bool:
        """Return whether the active official environment resolves one package."""
        # Why (mro-27a9e.1, multi-agent): standalone consumers inherit aliases
        # from installed FLEXT artifacts; plain modules are never facade parents.
        try:
            spec = importlib_util.find_spec(package_name)
        except c.EXC_OS_TYPE_VALUE:
            return False
        else:
            return spec is not None and spec.submodule_search_locations is not None

    @classmethod
    @cache
    def installed_package_exports(cls, package_name: str) -> frozenset[str]:
        """Return the explicit ABI published by one installed package root."""
        try:
            spec = importlib_util.find_spec(package_name)
        except c.EXC_OS_TYPE_VALUE:
            return frozenset()
        if spec is None or spec.submodule_search_locations is None or not spec.origin:
            return frozenset()
        init_path = Path(spec.origin)
        if not init_path.is_file():
            return frozenset()
        try:
            source = init_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        except OSError:
            return frozenset()
        return frozenset(cls.public_export_names_source(source))

    @classmethod
    def discover_python_dirs(
        cls, project_dir: Path, *, skip_dirs: frozenset[str] | None = None
    ) -> t.StrSequence:
        """Return top-level directories that contain at least one Python file."""
        if not project_dir.is_dir():
            return list[str]()
        effective_skip = (
            skip_dirs if skip_dirs is not None else c.Infra.PYTHON_DISCOVERY_SKIP_DIRS
        )
        workspace_excluded = cls._workspace_excluded_top_dirs(project_dir)
        return [
            subdir.name
            for subdir in sorted(project_dir.iterdir())
            if subdir.is_dir()
            and not subdir.name.startswith(".")
            and subdir.name not in effective_skip
            and subdir.name not in workspace_excluded
            and any(subdir.rglob(c.Infra.EXT_PYTHON_GLOB))
        ]

    @classmethod
    def analyzer_python_roots(
        cls, project_dir: Path, declared: t.StrSequence
    ) -> t.StrSequence:
        """Return the Python roots every analyzer surface must agree on.

        Conform, the deps modernizer and the extra-paths sync each described
        the same concept on their own: some filtered the declared ``env_dirs``
        by existence, others discovered roots on disk. A project owning a
        Python directory outside ``env_dirs`` therefore had that root written
        by one surface and erased by the next, so apply never reached a fixed
        point and check reported permanent drift. This is the single owner:
        declared roots keep their configured order, because a pre-write
        scaffold can only offer those, and discovery appends the remaining
        roots that actually exist, which is the only set an analyzer accepts.

        A directory owning a ``pyproject.toml`` is a project in its own right,
        never a root of this one: workspace subprojects are Python directories
        too, and each is analyzed under its own local configuration.
        """
        discovered = cls.discover_python_dirs(project_dir)
        return (
            *declared,
            *(
                root
                for root in discovered
                if root not in declared
                and not (project_dir / root / c.Infra.PYPROJECT_FILENAME).is_file()
            ),
        )

    @staticmethod
    def _workspace_excluded_top_dirs(project_dir: Path) -> frozenset[str]:
        """Return first segments of read-only external topology paths."""
        from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

        excluded = FlextInfraWorkspaceDetector.analysis_exclusion_paths(project_dir)
        if excluded.failure:
            msg = excluded.error or "workspace analysis scope is unavailable"
            raise ValueError(msg)
        return frozenset(path.parts[0] for path in excluded.value if path.parts)

    @staticmethod
    def package_init_path(workspace_root: Path, package_name: str) -> Path | None:
        """Resolve a package anywhere inside the selected Rope scan root."""
        package_parts = Path(*package_name.split("."))
        resolved_root = workspace_root.resolve()
        project_roots = {
            resolved_root,
            *(
                path.parent.resolve()
                for path in resolved_root.rglob(c.Infra.PYPROJECT_FILENAME)
                if not any(
                    part.startswith(".") or part in c.Infra.PYPROJECT_SKIP_DIRS
                    for part in path.relative_to(resolved_root).parts[:-1]
                )
            ),
        }
        candidates = (
            *(
                project_root / c.Infra.DEFAULT_SRC_DIR / package_parts / c.Infra.INIT_PY
                for project_root in sorted(project_roots)
            ),
        )
        for candidate in candidates:
            if candidate.is_file():
                return Path(candidate)
        return None

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

    @classmethod
    def rope_workspace_root(cls, workspace_root: Path) -> Path:
        """Return the execution-context root for one conditional Rope scan."""
        resolved_root = workspace_root.resolve()
        execution_dir = (
            resolved_root if resolved_root.is_dir() else resolved_root.parent
        )
        for candidate in (execution_dir, *execution_dir.parents):
            if (candidate / c.Infra.GITMODULES).is_file():
                return candidate.resolve()
        project_root = cls.project_root(resolved_root)
        if project_root is not None:
            return project_root
        return resolved_root

    @classmethod
    def find_all_pyproject_files(
        cls,
        workspace_root: Path,
        *,
        skip_dirs: frozenset[str] | None = None,
        project_paths: t.SequenceOf[Path] | None = None,
    ) -> p.Result[t.SequenceOf[Path]]:
        """Find all managed ``pyproject.toml`` files for one workspace root."""
        if not workspace_root.exists() or not workspace_root.is_dir():
            return r[t.SequenceOf[Path]].ok([])
        effective_skip = skip_dirs if skip_dirs is not None else c.Infra.SKIP_DIRS
        # Explicit project paths are a hard write-scope boundary. Without one,
        # discovery is strictly local to the repository supplied by the caller.
        scan_roots = (
            sorted({project_path.resolve() for project_path in project_paths})
            if project_paths is not None
            else [workspace_root.resolve()]
        )
        all_files: list[Path] = []
        for scan_root in scan_roots:
            if scan_root.is_file():
                if scan_root.name != c.Infra.PYPROJECT_FILENAME:
                    return r[t.SequenceOf[Path]].fail(
                        f"explicit project file must be {c.Infra.PYPROJECT_FILENAME}: {scan_root}"
                    )
                all_files.append(scan_root)
                continue
            if not scan_root.is_dir():
                return r[t.SequenceOf[Path]].fail(
                    f"explicit project path is not accessible: {scan_root}"
                )
            try:
                all_files.extend(
                    sorted(
                        path
                        for path in scan_root.rglob(c.Infra.PYPROJECT_FILENAME)
                        if not any(
                            part.startswith(".") or part in effective_skip
                            for part in path.relative_to(scan_root).parts[:-1]
                        )
                    )
                )
            except OSError as exc:
                return r[t.SequenceOf[Path]].fail_op("pyproject file scan", exc)
        if project_paths is not None:
            all_files = [
                path
                for path in all_files
                if any(
                    path.is_relative_to(project_path) for project_path in project_paths
                )
            ]
        return r[t.SequenceOf[Path]].ok(all_files)

    @classmethod
    def resolve_parent_constants_mro(
        cls, pkg_dir_or_file: Path, *, return_module: bool = False
    ) -> t.StrSequence:
        """Resolve imported parent ``Constants`` targets through Rope semantics."""
        constants_file = (
            pkg_dir_or_file
            if pkg_dir_or_file.name == c.Infra.CONSTANTS_PY
            else pkg_dir_or_file / c.Infra.CONSTANTS_PY
        )
        if not constants_file.is_file():
            return ()
        project_root = cls.project_root(constants_file)
        if project_root is None:
            return ()
        cache_key = (str(constants_file.resolve()), return_module)
        if (cached := cls._PARENT_CONSTANTS_MRO_CACHE.get(cache_key)) is not None:
            return cached
        current_module = cls.package_name(constants_file)
        result = cls.parent_constants_targets(
            constants_file,
            project_root,
            return_module=return_module,
            current_root=current_module.split(".", maxsplit=1)[0]
            if current_module
            else "",
        )
        cls._PARENT_CONSTANTS_MRO_CACHE[cache_key] = result
        return result

    @classmethod
    def resolve_transitive_parent_packages(
        cls, workspace_root: Path, package_names: t.StrSequence
    ) -> t.StrSequence:
        """Resolve parent packages transitively with ancestors ordered before children."""
        resolved: list[str] = []
        visited: set[str] = set()

        def visit(package_name: str) -> None:
            """Visit."""
            if not package_name or package_name in visited:
                return
            visited.add(package_name)
            init_path = cls.package_init_path(workspace_root, package_name)
            if init_path is not None:
                for parent_package in cls.resolve_parent_constants_mro(
                    init_path.parent, return_module=True
                ):
                    visit(parent_package)
            resolved.append(package_name)

        for package_name in package_names:
            visit(package_name)
        prioritized = cls.package_source_priority((*resolved, *package_names))
        return tuple(prioritized)

    @classmethod
    def contextual_runtime_alias_sources(
        cls, *, project_root: Path, file_path: Path
    ) -> t.MappingKV[str, frozenset[str]]:
        """Return allowed foreign-package runtime alias sources for one file."""
        package_name = cls.project_package_name(project_root)
        if not package_name:
            return {}
        package_dir = (
            project_root / c.Infra.DEFAULT_SRC_DIR / Path(*package_name.split("."))
        )
        if not (package_dir / c.Infra.INIT_PY).is_file():
            return {}
        parent_packages = cls.resolve_parent_constants_mro(
            package_dir, return_module=True
        )
        if not parent_packages:
            return {}
        transitive_parent_packages = cls.resolve_transitive_parent_packages(
            cls.rope_workspace_root(project_root), parent_packages
        )
        allowed_sources = frozenset(
            package.split(".", maxsplit=1)[0]
            for package in (*parent_packages, *transitive_parent_packages)
        )
        for family_dir in c.Infra.FAMILY_DIRECTORIES.values():
            if file_path.is_relative_to(package_dir / family_dir):
                return dict.fromkeys(c.Infra.MRO_FAMILIES, allowed_sources)
        if file_path.name in {"base.py", c.Infra.NAMESPACE_PRIVATE_BASE_MODULE}:
            return dict.fromkeys(c.Infra.ENFORCEMENT_CANONICAL_ALIASES, allowed_sources)
        if file_path.name in c.Infra.NAMESPACE_SETTINGS_FILE_NAMES:
            return dict.fromkeys(c.Infra.MRO_FAMILIES, allowed_sources)
        return {}


__all__: list[str] = ["FlextInfraUtilitiesDiscovery"]
