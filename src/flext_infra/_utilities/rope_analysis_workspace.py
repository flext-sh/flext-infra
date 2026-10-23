"""Rope workspace indexing helpers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import operator
from collections.abc import MutableMapping
from contextlib import ExitStack
from pathlib import Path

from flext_infra import c, config, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenFacades,
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesIterationDirectory,
    FlextInfraUtilitiesIterationWorkspace,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesRopeRuntime,
)
from flext_infra._utilities._rope_source_bases_aliases import (
    FlextInfraUtilitiesRopeSourceBasesAliases,
)
from flext_infra._utilities._rope_source_bases_runtime import (
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)


class FlextInfraUtilitiesRopeAnalysisWorkspace:
    """Rope-backed workspace indexing helpers."""

    @classmethod
    def generated_source_packages(cls, project_root: Path) -> t.StrTuple:
        """Return the import packages of a project's generated source trees.

        The tree names come from the codegen artifact key
        (``generated_source``); analyzers that take module names rather than
        path globs exclude exactly these packages.

        Returns:
            The sorted import packages of every generated source tree.

        """
        root = project_root.resolve()
        names = frozenset(config.Infra.codegen.generated_sources)
        ignored = FlextInfraUtilitiesProjectDiscovery.excluded_parts() - names
        packages: set[str] = set()
        for scan_root in config.Infra.source_scan.roots:
            base = root / scan_root
            if not base.is_dir():
                continue
            for name in names:
                for directory in base.rglob(name):
                    package = FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
                        directory, project_root=root
                    )
                    if (
                        directory.is_dir()
                        and package
                        and not ignored.intersection(directory.relative_to(root).parts)
                    ):
                        packages.add(package)
        return tuple(sorted(packages))

    @classmethod
    def module_name_for_file(cls, file_path: Path, *, project_root: Path) -> str:
        """Return the module name for a file.

        Returns:
            The module name for a file.

        """
        package_name = FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
            file_path.parent,
            project_root=project_root,
        )
        if file_path.name in {c.Infra.INIT_PY, c.Infra.INIT_PYI}:
            return package_name
        return f"{package_name}.{file_path.stem}" if package_name else ""

    @classmethod
    def runtime_evaluated_base_classes(
        cls,
        project_root: Path,
        planned_sources: t.MappingKV[Path, str],
        roots: t.StrSequence,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> t.StrTuple:
        """Return the class bases whose subclasses evaluate annotations at runtime.

        Captured source supplies declaration identities, while import bindings
        supply Ruff's qualified expressions. Planned bytes override disk and
        providers before aliases, members and ordered C3 parents are resolved.
        No project package is imported during generation.

        Returns:
            The declared roots and the derived bases, by qualified name.

        """
        root = project_root.resolve()
        with ExitStack() as stack:
            if source_project is None:
                source_project, _, captured = stack.enter_context(
                    FlextInfraUtilitiesCodegenFacades.facade_source_project(
                        root,
                        planned_sources=planned_sources,
                    )
                )
            else:
                captured = cls._project_sources(
                    root, planned_sources, source_project=source_project
                )
            sources = {
                cls.module_name_for_file(path, project_root=root): (path, source)
                for path, source in captured.items()
                if cls.module_name_for_file(path, project_root=root)
            }
            if not sources:
                return tuple(sorted(roots))
            # The original or proposed initializer owns each public alias.
            extra_module_aliases: t.StrDict = {}
            for init_module, (init_path, init_source) in sorted(sources.items()):
                if init_path.name != c.Infra.INIT_PY:
                    continue
                for (
                    alias,
                    absolute,
                ) in FlextInfraUtilitiesRopeSourceBasesAliases.lazy_module_aliases(
                    init_module,
                    init_path,
                    init_source,
                    project=source_project,
                ).items():
                    extra_module_aliases.setdefault(
                        f"{init_module}.{alias}",
                        absolute,
                    )
            return FlextInfraUtilitiesRopeSourceBasesRuntime.runtime_bases(
                source_project,
                sources,
                roots,
                extra_module_aliases=extra_module_aliases,
            )

    @staticmethod
    def _project_sources(
        root: Path,
        planned_sources: t.MappingKV[Path, str],
        *,
        source_project: p.Infra.RopeProject,
    ) -> t.MappingKV[Path, str]:
        """Read elected sources through the native graph before applying plans.

        Returns:
            Each source by resolved path.

        """
        planned = {path.resolve(): source for path, source in planned_sources.items()}
        files = (
            FlextInfraUtilitiesIterationWorkspace.iter_python_files(
                m.Infra.SourceScanRequest(project_roots=(root,)),
            ).unwrap()
            if root.is_dir()
            else ()
        )
        native_root = Path(source_project.root.real_path)
        sources: t.MutableMappingKV[Path, str] = {}
        for file_path in dict.fromkeys((*files, *planned)):
            path = file_path.resolve()
            if not path.is_relative_to(
                root
            ) or FlextInfraUtilitiesIterationDirectory.source_scan_ignored_path(
                root, path
            ):
                continue
            resource = source_project.get_resource(
                path.relative_to(native_root).as_posix()
            )
            source = FlextInfraUtilitiesRopeRuntime.require_file_resource(
                resource, path
            ).read()
            sources[path] = planned.get(path, source)
        return sources

    @staticmethod
    def _is_generated_init_stub(
        file_path: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> bool:
        """Return whether ``file_path`` is a codegen-owned package stub.

        Returns:
            Whether ``file_path`` is a codegen-owned package stub.

        """
        if file_path.name != c.Infra.INIT_PYI:
            return False
        source = (
            file_path.read_text(encoding=c.DEFAULT_ENCODING)
            if source_project is None
            else source_project.source_text(file_path)
        )
        return source.startswith(
            c.Infra.AUTOGEN_HEADERS,
        )

    @staticmethod
    def python_and_stub_file_paths(
        rope_project: t.Infra.RopeProject,
        resolved_root: Path,
    ) -> t.VariadicTuple[Path]:
        """Return this repository's sources without electing members as targets.

        Returns:
            Local Python and stub sources, preserving dependency import resolution.

        Raises:
            ValueError: The repository's Git member declarations are invalid.

        """
        rope_root = Path(rope_project.root.real_path).resolve()
        source_project = rope_project if rope_project.authenticated_sources else None
        declarations = FlextInfraUtilitiesGit.git_submodule_declarations(
            resolved_root, source_project=source_project
        )
        if declarations.failure:
            raise ValueError(declarations.error or "invalid .gitmodules")
        return tuple(
            path
            for path in FlextInfraUtilitiesProjectDiscovery.discover_python_files(
                resolved_root,
                workspace_excluded_top_dirs=frozenset(
                    item.path.as_posix() for item in declarations.value
                ),
                source_project=source_project,
            )
            if path.is_relative_to(rope_root)
        )

    @classmethod
    def _collect_modules(
        cls,
        rope_project: t.Infra.RopeProject,
        resolved_root: Path,
    ) -> tuple[
        MutableMapping[str, m.Infra.RopeModuleIndexEntry],
        MutableMapping[Path, list[m.Infra.RopeModuleIndexEntry]],
        MutableMapping[str, Path],
        MutableMapping[str, str],
        set[Path],
    ]:
        """Collect modules.

        Returns:
            The resulting ``tuple[MutableMapping[str, m.Infra.RopeModuleIndexEntry],
                MutableMapping[Path, list[m.Infra.RopeModuleIndexEntry]],
                MutableMapping[str, Path], MutableMapping[str, str], set[Path]]``.

        """
        modules_by_path: MutableMapping[str, m.Infra.RopeModuleIndexEntry] = {}
        modules_by_dir: MutableMapping[Path, list[m.Infra.RopeModuleIndexEntry]] = {}
        package_dir_by_name: MutableMapping[str, Path] = {}
        project_package_by_root: MutableMapping[str, str] = {}
        package_dirs: set[Path] = set()
        # Hermetic index: iterate the discovery output in sorted path order so
        # every derived structure (index, lazy maps, generated facades) is
        # byte-identical across environments regardless of fs enumeration.
        for file_path in sorted(
            cls.python_and_stub_file_paths(rope_project, resolved_root),
            key=str,
        ):
            resolved_file_path = file_path.resolve()
            if cls._is_generated_init_stub(
                resolved_file_path,
                source_project=rope_project
                if rope_project.authenticated_sources
                else None,
            ):
                continue
            if not resolved_file_path.is_relative_to(resolved_root):
                continue
            if FlextInfraUtilitiesProjectDiscovery.excluded_parts().intersection(
                resolved_file_path.relative_to(resolved_root).parts[:-1],
            ):
                # The scan-ignore SSOT owns source visibility everywhere: a
                # tool hook under an ignored resource (e.g. .claude, .agents)
                # is not a project module, and indexing it feeds the mod
                # planners a file they then crash on while moving helpers.
                continue
            resource_path = resolved_file_path.relative_to(resolved_root).as_posix()
            package_dir = resolved_file_path.parent
            is_package_init = resolved_file_path.name in {
                c.Infra.INIT_PY,
                c.Infra.INIT_PYI,
            }
            project_root = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
                Path(rope_project.root.real_path),
                resolved_file_path,
                source_project=rope_project
                if rope_project.authenticated_sources
                else None,
            )
            module_name = (
                cls.module_name_for_file(resolved_file_path, project_root=project_root)
                if project_root is not None
                else ""
            )
            package_name = (
                FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
                    package_dir, project_root=project_root
                )
                if project_root is not None
                else module_name
                if is_package_init
                else module_name.rsplit(".", maxsplit=1)[0]
                if "." in module_name
                else ""
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
        return (
            modules_by_path,
            modules_by_dir,
            package_dir_by_name,
            project_package_by_root,
            package_dirs,
        )

    @staticmethod
    def _package_family_maps(
        sorted_package_dirs: t.VariadicTuple[Path],
    ) -> t.Pair[
        MutableMapping[Path, list[Path]],
        MutableMapping[Path, list[Path]],
    ]:
        """Map every package dir to its direct-child and descendant package dirs.

        Returns:
            The resulting ``(direct children, descendants)`` map pair.

        """
        package_dir_set = frozenset(sorted_package_dirs)
        direct_children_by_dir: MutableMapping[Path, list[Path]] = {
            package_dir: [] for package_dir in sorted_package_dirs
        }
        descendants_by_dir: MutableMapping[Path, list[Path]] = {
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
        return direct_children_by_dir, descendants_by_dir

    @classmethod
    def _package_identity(
        cls,
        package_dir: Path,
        modules_by_dir: t.MappingKV[Path, list[m.Infra.RopeModuleIndexEntry]],
        modules_by_path: t.MappingKV[str, m.Infra.RopeModuleIndexEntry],
    ) -> t.Quad[
        t.VariadicTuple[m.Infra.RopeModuleIndexEntry],
        Path,
        Path | None,
        str,
    ]:
        """Resolve one package's modules, init path, project root, and name.

        Returns:
            The resulting ``(sorted modules, init path, project root, name)``.

        """
        dir_modules = tuple(
            sorted(
                modules_by_dir.get(package_dir, ()),
                key=operator.attrgetter("file_path.name"),
            ),
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
            FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
                package_dir, project_root=project_root
            )
            if project_root is not None
            else init_entry.package_name
            if init_entry is not None
            else ""
        )
        return dir_modules, init_path, project_root, package_name

    @staticmethod
    def _register_package_identity(
        package_dir: Path,
        project_root: Path | None,
        package_name: str,
        package_dir_by_name: MutableMapping[str, Path],
        project_package_by_root: MutableMapping[str, str],
    ) -> None:
        """Record one package's name in the index maps when it is new."""
        if package_name and package_name not in package_dir_by_name:
            package_dir_by_name[package_name] = package_dir
        if (
            project_root is not None
            and "." not in package_name
            and package_dir.parent.name == c.Infra.DEFAULT_SRC_DIR
            and str(project_root) not in project_package_by_root
        ):
            project_package_by_root[str(project_root)] = package_name

    @classmethod
    def index_rope_workspace(
        cls,
        rope_project: t.Infra.RopeProject,
        repository_root: Path,
    ) -> m.Infra.RopeWorkspaceIndex:
        """Build a generic Rope workspace index for package-oriented planning.

        Returns:
            The resulting ``m.Infra.RopeWorkspaceIndex``.

        """
        resolved_root = repository_root.resolve()
        (
            modules_by_path,
            modules_by_dir,
            package_dir_by_name,
            project_package_by_root,
            package_dirs,
        ) = cls._collect_modules(rope_project, resolved_root)
        sorted_package_dirs = tuple(sorted(package_dirs))
        direct_children_by_dir, descendants_by_dir = cls._package_family_maps(
            sorted_package_dirs,
        )
        packages_by_dir: MutableMapping[str, m.Infra.RopePackageIndexEntry] = {}
        for package_dir in sorted_package_dirs:
            (
                dir_modules,
                init_path,
                project_root,
                package_name,
            ) = cls._package_identity(package_dir, modules_by_dir, modules_by_path)
            cls._register_package_identity(
                package_dir,
                project_root,
                package_name,
                package_dir_by_name,
                project_package_by_root,
            )
            packages_by_dir[str(package_dir)] = m.Infra.RopePackageIndexEntry(
                package_dir=package_dir,
                init_path=init_path,
                package_name=package_name,
                project_root=project_root,
                modules=dir_modules,
                direct_child_dirs=tuple(direct_children_by_dir.get(package_dir, ())),
                descendant_child_dirs=tuple(descendants_by_dir.get(package_dir, ())),
            )
        return m.Infra.RopeWorkspaceIndex(
            repository_root=resolved_root,
            package_dirs=sorted_package_dirs,
            packages_by_dir=packages_by_dir,
            modules_by_path=modules_by_path,
            package_dir_by_name=package_dir_by_name,
            project_package_by_root=project_package_by_root,
        )


__all__: list[str] = ["FlextInfraUtilitiesRopeAnalysisWorkspace"]
