"""Rope workspace indexing helpers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import operator
from collections.abc import Mapping, MutableMapping, Sequence
from contextlib import ExitStack
from pathlib import Path

from flext_infra import c, config, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesIterationDirectory,
    FlextInfraUtilitiesIterationWorkspace,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime
from flext_infra._utilities._rope.rope_source_bases_runtime import (
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities._rope.source_bases_aliases import (
    FlextInfraUtilitiesRopeSourceBasesAliases,
)


class FlextInfraUtilitiesRopeAnalysisWorkspace:
    """Rope-backed workspace indexing helpers."""

    @classmethod
    def generated_source_packages(cls, project_root: Path) -> t.StrTuple:
        """Return the import packages of a project's generated source trees.

        The tree names come from the codegen artifact key
        (``generated_source``). This is generation-ownership inventory, not
        analyzer applicability or proof of third-party provenance.

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
    def runtime_evaluated_base_classes(
        cls,
        project_root: Path,
        planned_sources: Mapping[Path, str],
        roots: Sequence[str],
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
                source_project, captured = stack.enter_context(
                    FlextInfraUtilitiesWorkspaceSnapshot.facade_source_project(
                        root,
                        planned_sources=planned_sources,
                    )
                )
            else:
                captured = cls._project_sources(
                    root, planned_sources, source_project=source_project
                )
            native_roots = {
                Path(folder.real_path) for folder in source_project.get_source_folders()
            }
            provider_roots = tuple(
                Path(folder.real_path)
                for folder in source_project.get_python_path_folders()
                if Path(folder.real_path) not in native_roots
                and Path(folder.real_path).is_relative_to(root)
            )
            planned = frozenset(path.resolve() for path in planned_sources)
            sources: MutableMapping[str, tuple[Path, str]] = {}
            for path, source in captured.items():
                # Providers remain in their native import election, not the owned
                # declaration census. Explicit plans retain their authority.
                if path not in planned and any(
                    path.is_relative_to(provider_root)
                    for provider_root in provider_roots
                ):
                    continue
                module = FlextInfraUtilitiesProjectDiscovery.module_name_for_file(
                    path, project_root=root, source_project=source_project
                )
                if module:
                    sources[module] = path, source
            if not sources:
                return tuple(sorted(roots))
            # The original or proposed initializer owns each public alias.
            extra_module_aliases: dict[str, str] = {}
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
        planned_sources: Mapping[Path, str],
        *,
        source_project: p.Infra.RopeProject,
    ) -> Mapping[Path, str]:
        """Read each source from its declared plan or original native owner.

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
        sources: MutableMapping[Path, str] = {}
        for file_path in dict.fromkeys((*files, *planned)):
            path = file_path.resolve()
            if not path.is_relative_to(
                root
            ) or FlextInfraUtilitiesIterationDirectory.source_scan_ignored_path(
                root, path
            ):
                continue
            if path in planned:
                sources[path] = planned[path]
                continue
            resource = source_project.get_resource(
                path.relative_to(native_root).as_posix()
            )
            source = FlextInfraUtilitiesRopeRuntime.require_file_resource(
                resource, path
            ).read()
            sources[path] = source
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
            c.Infra.AUTOGEN_HEADER,
        )

    @classmethod
    def _module_entry(
        cls,
        file_path: Path,
        resolved_root: Path,
        rope_project: t.Infra.RopeProject,
        directory_facts: MutableMapping[Path, tuple[Path | None, str]],
    ) -> m.Infra.RopeModuleIndexEntry | None:
        """Index one source, or ``None`` for a generated stub or an ignored path.

        The owning project and the declared package depend on the directory
        only, so every module of a directory shares one lookup.

        Returns:
            The module's index entry, or ``None`` when it is not a project module.

        """
        resolved_file_path = file_path.resolve()
        if cls._is_generated_init_stub(
            resolved_file_path, source_project=rope_project
        ) or not resolved_file_path.is_relative_to(resolved_root):
            return None
        if FlextInfraUtilitiesProjectDiscovery.excluded_parts().intersection(
            resolved_file_path.relative_to(resolved_root).parts[:-1],
        ):
            # The scan-ignore SSOT owns source visibility everywhere: a
            # tool hook under an ignored resource (e.g. .claude, .agents)
            # is not a project module, and indexing it feeds the mod
            # planners a file they then crash on while moving helpers.
            return None
        package_dir = resolved_file_path.parent
        is_package_init = resolved_file_path.name in {c.Infra.INIT_PY, c.Infra.INIT_PYI}
        owner = directory_facts.get(package_dir)
        if owner is None:
            directory_root = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
                Path(rope_project.root.real_path),
                resolved_file_path,
                source_project=rope_project,
            )
            owner = (
                directory_root,
                FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
                    package_dir,
                    project_root=directory_root,
                    source_project=rope_project,
                )
                if directory_root is not None
                else "",
            )
            directory_facts[package_dir] = owner
        project_root, package_name = owner
        return m.Infra.RopeModuleIndexEntry(
            file_path=resolved_file_path,
            resource_path=resolved_file_path.relative_to(resolved_root).as_posix(),
            module_name=(
                FlextInfraUtilitiesProjectDiscovery.module_name_for_file(
                    resolved_file_path,
                    project_root=project_root,
                    source_project=rope_project,
                )
                if project_root is not None
                else ""
            ),
            package_name=package_name,
            package_dir=package_dir,
            project_root=project_root,
            is_package_init=is_package_init,
        )

    @classmethod
    def _collect_modules(
        cls,
        rope_project: t.Infra.RopeProject,
        resolved_root: Path,
        files: tuple[Path, ...],
        directory_facts: MutableMapping[Path, tuple[Path | None, str]],
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
        entries: list[m.Infra.RopeModuleIndexEntry] = []
        for file_path in sorted(files, key=str):
            entry = cls._module_entry(
                file_path, resolved_root, rope_project, directory_facts
            )
            if entry is not None:
                entries.append(entry)
        return cls._module_maps(entries)

    @staticmethod
    def _module_maps(
        entries: Sequence[m.Infra.RopeModuleIndexEntry],
    ) -> tuple[
        MutableMapping[str, m.Infra.RopeModuleIndexEntry],
        MutableMapping[Path, list[m.Infra.RopeModuleIndexEntry]],
        MutableMapping[str, Path],
        MutableMapping[str, str],
        set[Path],
    ]:
        """Aggregate elected entries without rediscovering unchanged resources.

        Returns:
            The module and package maps of the existing structural index.

        """
        modules_by_path: MutableMapping[str, m.Infra.RopeModuleIndexEntry] = {}
        modules_by_dir: MutableMapping[Path, list[m.Infra.RopeModuleIndexEntry]] = {}
        package_dir_by_name: MutableMapping[str, Path] = {}
        project_package_by_root: MutableMapping[str, str] = {}
        package_dirs: set[Path] = set()
        # Hermetic index: iterate the discovery output in sorted path order so
        # every derived structure (index, lazy maps, generated facades) is
        # byte-identical across environments regardless of fs enumeration.
        for entry in sorted(entries, key=operator.attrgetter("file_path")):
            resolved_file_path = entry.file_path
            package_dir = entry.package_dir
            package_name = entry.package_name
            project_root = entry.project_root
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
        sorted_package_dirs: tuple[Path, ...],
    ) -> tuple[
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
        modules_by_dir: Mapping[Path, list[m.Infra.RopeModuleIndexEntry]],
        modules_by_path: Mapping[str, m.Infra.RopeModuleIndexEntry],
    ) -> tuple[
        tuple[m.Infra.RopeModuleIndexEntry, ...],
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
            init_entry.package_name
            if init_entry is not None
            else next((entry.package_name for entry in dir_modules), "")
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
        snapshot: p.Infra.WorkspaceSnapshot,
        repository_root: Path,
        *,
        project: p.Infra.RopeProject | None = None,
        project_roots: Sequence[Path] | None = None,
        previous_index: m.Infra.RopeWorkspaceIndex | None = None,
        changed_paths: Sequence[Path] = (),
    ) -> m.Infra.RopeWorkspaceIndex:
        """Build a Rope workspace index as a view over the run snapshot's listing.

        The root and every member the snapshot holds below it are elected
        sources unless explicit repository roots bind a scoped query.
        ``project`` lists through a planned view instead of the snapshot engine.
        A previously elected index evolves only the supplied changed paths;
        unchanged resources keep their native module-entry identities.

        Returns:
            The resulting ``m.Infra.RopeWorkspaceIndex``.

        Raises:
            ValueError: A supplied previous index belongs to another repository.

        """
        resolved_root = repository_root.resolve()
        source_project = snapshot.engine if project is None else project
        if previous_index is not None:
            if previous_index.repository_root != resolved_root:
                message = "incremental Rope index belongs to another repository"
                raise ValueError(message)
            entries = dict(previous_index.modules_by_path)
            directory_facts: MutableMapping[Path, tuple[Path | None, str]] = {}
            changed = {path.resolve() for path in changed_paths}
            metadata_roots = {
                path.parent for path in changed if path.name == c.PYPROJECT_FILENAME
            }
            changed.update(
                entry.file_path
                for entry in entries.values()
                if entry.project_root in metadata_roots
            )
            for path in changed:
                resolved_path = path.resolve()
                entries.pop(str(resolved_path), None)
                if (
                    resolved_path.suffix not in c.Infra.PYTHON_SOURCE_SUFFIXES
                    or not source_project.source_query(resolved_path, "isfile")
                ):
                    continue
                entry = cls._module_entry(
                    resolved_path, resolved_root, source_project, directory_facts
                )
                if entry is not None:
                    entries[str(resolved_path)] = entry
            if entries == previous_index.modules_by_path:
                return previous_index
            collected = cls._module_maps(tuple(entries.values()))
        else:
            listing = tuple(
                path
                for member in (
                    tuple(project_roots)
                    if project_roots is not None
                    else (
                        resolved_root,
                        *(
                            other
                            for other in snapshot.members
                            if other != resolved_root
                            and other.is_relative_to(resolved_root)
                        ),
                    )
                )
                for path in FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(
                    snapshot, member, project=project
                )
            )
            collected = cls._collect_modules(
                source_project,
                resolved_root,
                listing,
                snapshot.directory_facts if project is None else {},
            )
        (
            modules_by_path,
            modules_by_dir,
            package_dir_by_name,
            project_package_by_root,
            package_dirs,
        ) = collected
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
            previous_package = (
                previous_index.packages_by_dir.get(str(package_dir))
                if previous_index is not None
                else None
            )
            children = tuple(direct_children_by_dir.get(package_dir, ()))
            descendants = tuple(descendants_by_dir.get(package_dir, ()))
            if (
                previous_package is not None
                and previous_package.init_path == init_path
                and previous_package.package_name == package_name
                and previous_package.project_root == project_root
                and previous_package.modules == dir_modules
                and previous_package.direct_child_dirs == children
                and previous_package.descendant_child_dirs == descendants
            ):
                packages_by_dir[str(package_dir)] = previous_package
                continue
            packages_by_dir[str(package_dir)] = m.Infra.RopePackageIndexEntry(
                package_dir=package_dir,
                init_path=init_path,
                package_name=package_name,
                project_root=project_root,
                modules=dir_modules,
                direct_child_dirs=children,
                descendant_child_dirs=descendants,
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
