"""Runtime import graph and cycle facts for FlextInfraUtilitiesCodemodProject.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from time import monotonic

from flext_cli import settings, u

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesIterationDirectory,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesRopeAnalysisWorkspace,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._rope_analysis.importstate import (
    FlextInfraUtilitiesRopeAnalysisImportState,
)
from flext_infra._utilities._rope_source_bases_aliases import (
    FlextInfraUtilitiesRopeSourceBasesAliases,
)


class FlextInfraUtilitiesCodemodProjectImportGraphMixin:
    """Build the runtime import graph and grade import-cycle edges."""

    @staticmethod
    def codemod_progress(message: str, due: float = 0) -> float:
        """Report active source work at the configured heartbeat interval.

        Returns:
            The next monotonic deadline for an interval progress row.

        """
        now = monotonic()
        if now < due:
            return due
        u.Cli.info(f"mod: {message}")
        return now + settings.cli_process_heartbeat_seconds

    @classmethod
    def project_import_graph(
        cls,
        root: Path,
    ) -> t.Pair[t.MappingKV[str, frozenset[str]], t.MappingKV[Path, str]]:
        """Return the runtime import graph and the module name of each file.

        Edges come from Rope's module-level import table, which leaves
        ``if TYPE_CHECKING:`` imports and function-local imports out: only
        imports that run when the module loads can form a cycle. Each target
        is truncated to the longest module the project defines.

        Live nodes use the workspace indexer's governed inventory, not Rope's
        recursive checkout enumeration. Declared members retain their import
        roots; unrelated checkouts and managed projections are not graph nodes.

        Returns:
            The runtime import graph and the module name of each file.

        """
        resolved = root.resolve()
        with FlextInfraUtilitiesRopeCore.open_project(
            resolved,
            project_roots=FlextInfraUtilitiesProjectDiscovery.governed_project_roots(
                resolved,
            ),
        ) as project:
            resources = tuple(
                FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                    project.get_resource(path.relative_to(resolved).as_posix()),
                    path,
                )
                for path in (
                    FlextInfraUtilitiesRopeAnalysisWorkspace.python_and_stub_file_paths(
                        project,
                        resolved,
                    )
                )
                if path.suffix == c.Infra.EXT_PYTHON
            )
            return cls.snapshot_import_graph(project, resources=resources)

    @classmethod
    def snapshot_import_graph(
        cls,
        project: p.Infra.RopeProject,
        *,
        resources: t.SequenceOf[t.Infra.RopeFile] | None = None,
    ) -> t.Pair[t.MappingKV[str, frozenset[str]], t.MappingKV[Path, str]]:
        """Read runtime imports from an immutable proposed-source Rope graph.

        A live caller supplies governed resources. An immutable snapshot keeps
        its complete captured inventory, including proposed virtual modules.

        Returns:
            The resulting ``t.Pair[t.MappingKV[str, frozenset[str]], t.MappingKV[Path,
                str]]``.

        Raises:
            ValueError: If rope could not name module.

        """
        raw: MutableMapping[str, set[str]] = {}
        modules: MutableMapping[Path, str] = {}
        aliases: MutableMapping[str, str] = {}
        cls.codemod_progress("import graph start")
        due = 0.0
        for resource in (
            FlextInfraUtilitiesRopeCore.python_resources(project)
            if resources is None
            else resources
        ):
            due = cls.codemod_progress(
                f"import graph modules={len(modules)} file={resource.path}",
                due,
            )
            pymodule = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
            name = pymodule.get_name()
            if not name:
                msg = f"rope could not name module {resource.path}"
                raise ValueError(msg)
            path = Path(resource.real_path).resolve()
            modules[path] = name
            package = name if path.name == c.Infra.INIT_PY else name.rpartition(".")[0]
            raw[name] = set(
                FlextInfraUtilitiesRopeImports.imported_module_paths(
                    FlextInfraUtilitiesRopeCore.resolve_module_imports(
                        project,
                        resource,
                    ),
                    current_package=package,
                ),
            )
            # Requesting a lazy export loads its elected provider module. Merely
            # installing the map does not load every provider in the package.
            provider_aliases = (
                FlextInfraUtilitiesRopeSourceBasesAliases.lazy_module_aliases(
                    name,
                    path,
                    resource.read(),
                )
            )
            aliases.update({
                f"{name}.{export}": provider
                for export, provider in provider_aliases.items()
            })
        known = frozenset(raw)
        cls.codemod_progress(f"import graph finish modules={len(modules)}")
        graph = {
            name: frozenset(
                target
                for imported in targets
                if (target := cls._known_prefix(aliases.get(imported, imported), known))
                is not None
                and target != name
            )
            for name, targets in raw.items()
        }
        return graph, modules

    @staticmethod
    def project_import_cycles(
        graph: t.MappingKV[str, frozenset[str]],
    ) -> t.MappingKV[str, frozenset[str]]:
        """Map each module in a runtime import cycle to its cycle's members.

        Returns:
            The resulting ``t.MappingKV[str, frozenset[str]]``.

        """
        cycles: MutableMapping[str, frozenset[str]] = {}
        for component in FlextInfraUtilitiesBase.strongly_connected_components({
            name: set(targets) for name, targets in graph.items()
        }):
            members = frozenset(component)
            if len(members) > 1:
                cycles.update(dict.fromkeys(members, members))
        return cycles

    @classmethod
    def import_closes_cycle(
        cls,
        root: Path,
        file_path: Path,
        imported: str,
        name: str | None,
        facts: m.Infra.CodemodProjectFacts,
    ) -> bool:
        """Return whether one import of ``file_path`` is an edge of a cycle.

        ``imported`` is the import's module as written (relative dots
        included); ``name`` is the imported name of a from-import, which is
        itself a module when the statement imports a submodule.

        Returns:
            Whether one import of ``file_path`` is an edge of a cycle.

        Raises:
            ValueError: If a production module under the package source root is
                absent from the project import graph.

        """
        graph, modules = facts.import_graph, facts.import_modules
        source = modules.get(file_path.resolve())
        if source is None:
            layout = FlextInfraUtilitiesCodegenNamespace.layout(root)
            # Project-level files and trees the source scan already ignores
            # (codegen ``source_scan_ignored``, including ``legado``) have no
            # import-graph node. They are not missing production modules, so
            # an import in one cannot close a cycle of the scanned graph.
            if (
                layout is not None
                and file_path.is_relative_to(layout.src_dir)
                and not FlextInfraUtilitiesIterationDirectory.source_scan_ignored_path(
                    root.resolve(), file_path.resolve()
                )
            ):
                msg = (
                    f"source module is absent from the project import graph: "
                    f"{file_path}"
                )
                raise ValueError(msg)
            return False
        package = (
            source if file_path.name == c.Infra.INIT_PY else source.rpartition(".")[0]
        )
        level = len(imported) - len(imported.lstrip("."))
        absolute = (
            FlextInfraUtilitiesRopeAnalysisImportState.resolve_import_module(
                current_package=package,
                module_name=imported.lstrip("."),
                level=level,
            )
            if level
            else imported
        ) or package
        known = frozenset(graph)
        candidates = (f"{absolute}.{name}", absolute) if name else (absolute,)
        target = next(
            (
                found
                for candidate in candidates
                if (found := cls._known_prefix(candidate, known)) is not None
            ),
            None,
        )
        members = facts.import_cycles.get(source, frozenset())
        return target is not None and target != source and target in members

    @staticmethod
    def _known_prefix(module: str, known: frozenset[str]) -> str | None:
        """Return the longest dotted prefix of ``module`` the project defines.

        Returns:
            The longest dotted prefix of ``module`` the project defines.

        """
        parts = module.split(".")
        for size in range(len(parts), 0, -1):
            candidate = ".".join(parts[:size])
            if candidate in known:
                return candidate
        return None


__all__: list[str] = ["FlextInfraUtilitiesCodemodProjectImportGraphMixin"]
