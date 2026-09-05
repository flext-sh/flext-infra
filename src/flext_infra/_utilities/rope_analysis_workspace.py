"""Rope workspace indexing helpers."""

from __future__ import annotations

import operator
from pathlib import Path
from time import perf_counter

from flext_cli import u
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t


class FlextInfraUtilitiesRopeAnalysisWorkspace:
    """Rope-backed workspace indexing helpers."""

    @classmethod
    def _package_name_for_dir(cls, package_dir: Path, *, project_root: Path) -> str:
        """Package name for dir."""
        try:
            relative_parts = package_dir.relative_to(project_root).parts
        except ValueError:
            return ""
        if not relative_parts:
            return ""
        root_name = relative_parts[0]
        if root_name == c.Infra.DEFAULT_SRC_DIR:
            package_parts = relative_parts[1:]
        elif root_name in c.Infra.ROOT_WRAPPER_SEGMENTS:
            package_parts = relative_parts
        else:
            package_parts = ()
        return ".".join(package_parts)

    @classmethod
    def _module_name_for_file(cls, file_path: Path, *, project_root: Path) -> str:
        """Return the module name for a file."""
        if file_path.name in {c.Infra.INIT_PY, c.Infra.INIT_PYI}:
            return cls._package_name_for_dir(
                file_path.parent, project_root=project_root
            )
        package_name = cls._package_name_for_dir(
            file_path.parent, project_root=project_root
        )
        return f"{package_name}.{file_path.stem}" if package_name else ""

    @staticmethod
    def _is_generated_init_stub(file_path: Path) -> bool:
        """Return whether ``file_path`` is a codegen-owned package stub."""
        if file_path.name != c.Infra.INIT_PYI:
            return False
        return file_path.read_text(encoding=c.Cli.ENCODING_DEFAULT).startswith(
            c.Infra.AUTOGEN_HEADERS
        )

    @staticmethod
    def _python_and_stub_files(resolved_root: Path) -> tuple[tuple[Path, Path], ...]:
        """Return owned Python paths paired with their declared project root."""
        project_roots = {
            resolved_root,
            *FlextInfraUtilitiesProjectDiscovery.discover_rope_project_roots(
                resolved_root
            ),
        }
        scan_roots = {c.Infra.DEFAULT_SRC_DIR, *c.Infra.ROOT_WRAPPER_SEGMENTS}
        files: set[tuple[Path, Path]] = set()
        for project_root in sorted(project_roots):
            for root_name in sorted(scan_roots):
                source_root = project_root / root_name
                if not source_root.is_dir():
                    continue
                for parent, child_dirs, file_names in source_root.walk():
                    child_dirs[:] = [
                        name
                        for name in child_dirs
                        if not name.startswith(".")
                        and name not in c.Infra.ITERATION_EXCLUDED_PARTS
                    ]
                    files.update(
                        (parent / file_name, project_root)
                        for file_name in file_names
                        if file_name.endswith((".py", ".pyi"))
                    )
        return tuple(sorted(files, key=lambda item: item[0].as_posix()))

    @classmethod
    def _collect_modules(
        cls, rope_project: t.Infra.RopeProject, resolved_root: Path
    ) -> tuple[
        dict[str, m.Infra.RopeModuleIndexEntry],
        dict[Path, list[m.Infra.RopeModuleIndexEntry]],
        dict[str, Path],
        dict[str, str],
        set[Path],
    ]:
        """Collect modules."""
        started_at = perf_counter()
        modules_by_path: dict[str, m.Infra.RopeModuleIndexEntry] = {}
        modules_by_dir: dict[Path, list[m.Infra.RopeModuleIndexEntry]] = {}
        package_dir_by_name: dict[str, Path] = {}
        project_package_by_root: dict[str, str] = {}
        package_dirs: set[Path] = set()
        _ = rope_project
        files = cls._python_and_stub_files(resolved_root)
        u.Cli.info(
            f"rope: enumerated {len(files)} python modules in "
            f"{perf_counter() - started_at:.2f}s"
        )
        collection_started_at = perf_counter()
        for index, (resolved_file_path, project_root) in enumerate(files, start=1):
            if cls._is_generated_init_stub(resolved_file_path):
                continue
            try:
                resource_path = resolved_file_path.relative_to(resolved_root).as_posix()
            except ValueError:
                continue
            package_dir = resolved_file_path.parent
            is_package_init = resolved_file_path.name in {
                c.Infra.INIT_PY,
                c.Infra.INIT_PYI,
            }
            module_name = cls._module_name_for_file(
                resolved_file_path, project_root=project_root
            )
            package_name = cls._package_name_for_dir(
                package_dir, project_root=project_root
            )
            entry = m.Infra.RopeModuleIndexEntry(
                file_path=resolved_file_path,
                resource_path=resource_path,
                module_name=module_name,
                package_name=package_name,
                package_dir=package_dir,
                project_root=project_root,
                is_package_init=is_package_init,
            )
            modules_by_path[str(resolved_file_path)] = entry
            modules_by_dir.setdefault(package_dir, []).append(entry)
            package_dirs.add(package_dir)
            if package_name:
                package_dir_by_name[package_name] = package_dir
                if (
                    project_root is not None
                    and "." not in package_name
                    and package_dir.parent.name == c.Infra.DEFAULT_SRC_DIR
                ):
                    project_package_by_root[str(project_root)] = package_name
            if index % 1000 == 0:
                u.Cli.info(f"rope: collected {index}/{len(files)} module entries")
        u.Cli.info(
            f"rope: collected {len(files)} module entries in "
            f"{perf_counter() - collection_started_at:.2f}s"
        )
        return (
            modules_by_path,
            modules_by_dir,
            package_dir_by_name,
            project_package_by_root,
            package_dirs,
        )

    @classmethod
    def index_rope_workspace(
        cls, rope_project: t.Infra.RopeProject, repository_root: Path
    ) -> m.Infra.RopeWorkspaceIndex:
        """Build a generic Rope workspace index for package-oriented planning."""
        started_at = perf_counter()
        resolved_root = repository_root.resolve()
        (
            modules_by_path,
            modules_by_dir,
            package_dir_by_name,
            project_package_by_root,
            package_dirs,
        ) = cls._collect_modules(rope_project, resolved_root)
        u.Cli.info(f"rope: module index ready in {perf_counter() - started_at:.2f}s")
        hierarchy_started_at = perf_counter()
        sorted_package_dirs = tuple(sorted(package_dirs))
        package_dir_set = frozenset(sorted_package_dirs)
        direct_children_by_dir: dict[Path, list[Path]] = {
            package_dir: [] for package_dir in sorted_package_dirs
        }
        descendants_by_dir: dict[Path, list[Path]] = {
            package_dir: [] for package_dir in sorted_package_dirs
        }
        for package_dir in sorted_package_dirs:
            parent_dir = package_dir.parent
            if parent_dir in package_dir_set:
                direct_children_by_dir[parent_dir].append(package_dir)
            for ancestor_dir in package_dir.parents:
                if ancestor_dir == package_dir:
                    continue
                if ancestor_dir in package_dir_set:
                    descendants_by_dir[ancestor_dir].append(package_dir)
        u.Cli.info(
            f"rope: package hierarchy ready in "
            f"{perf_counter() - hierarchy_started_at:.2f}s"
        )
        aggregation_started_at = perf_counter()
        packages_by_dir: dict[str, m.Infra.RopePackageIndexEntry] = {}
        for package_dir in sorted_package_dirs:
            dir_modules = tuple(
                sorted(
                    modules_by_dir.get(package_dir, ()),
                    key=operator.attrgetter("file_path.name"),
                )
            )
            init_path = (package_dir / c.Infra.INIT_PY).resolve()
            init_entry = modules_by_path.get(str(init_path))
            project_root = (
                init_entry.project_root
                if init_entry is not None
                else next(
                    (
                        entry.project_root
                        for entry in dir_modules
                        if entry.project_root is not None
                    ),
                    None,
                )
            )
            package_name = (
                cls._package_name_for_dir(package_dir, project_root=project_root)
                if project_root is not None
                else init_entry.package_name
                if init_entry is not None
                else ""
            )
            if package_name and package_name not in package_dir_by_name:
                package_dir_by_name[package_name] = package_dir
            if (
                project_root is not None
                and "." not in package_name
                and package_dir.parent.name == c.Infra.DEFAULT_SRC_DIR
                and str(project_root) not in project_package_by_root
            ):
                project_package_by_root[str(project_root)] = package_name
            direct_child_dirs = tuple(direct_children_by_dir.get(package_dir, ()))
            descendant_child_dirs = tuple(descendants_by_dir.get(package_dir, ()))
            packages_by_dir[str(package_dir)] = m.Infra.RopePackageIndexEntry(
                package_dir=package_dir,
                init_path=init_path,
                package_name=package_name,
                project_root=project_root,
                modules=dir_modules,
                direct_child_dirs=direct_child_dirs,
                descendant_child_dirs=descendant_child_dirs,
            )
        u.Cli.info(
            f"rope: aggregated {len(packages_by_dir)} packages in "
            f"{perf_counter() - aggregation_started_at:.2f}s"
        )
        validation_started_at = perf_counter()
        workspace_index = m.Infra.RopeWorkspaceIndex(
            repository_root=resolved_root,
            package_dirs=sorted_package_dirs,
            packages_by_dir=packages_by_dir,
            modules_by_path=modules_by_path,
            package_dir_by_name=package_dir_by_name,
            project_package_by_root=project_package_by_root,
        )
        u.Cli.info(
            f"rope: validated workspace index in "
            f"{perf_counter() - validation_started_at:.2f}s"
        )
        return workspace_index


__all__: list[str] = ["FlextInfraUtilitiesRopeAnalysisWorkspace"]
