"""Runtime import graphs from the canonical captured source engine.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path

from flext_cli import u

from flext_infra import c, p, t
from flext_infra._utilities import FlextInfraUtilitiesProjectDiscovery
from flext_infra._utilities._import_law import FlextInfraUtilitiesImportLawPolicy
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeSourceBasesAliases,
)


class FlextInfraUtilitiesImportLawGraph(FlextInfraUtilitiesImportLawPolicy):
    """Read and validate the runtime graph, including requested lazy providers."""

    @classmethod
    def snapshot_import_graph(
        cls,
        project: p.Infra.RopeProject,
        *,
        resources: t.SequenceOf[t.Infra.RopeFile] | None = None,
    ) -> t.Pair[t.MappingKV[str, frozenset[str]], t.MappingKV[Path, str]]:
        """Read runtime imports from an immutable proposed-source Rope graph.

        A live caller supplies governed resources. An authenticated candidate
        elects its complete native Python source scope before constructing
        resources; provider receipts do not enlarge that scope. An immutable
        snapshot keeps its captured inventory, including proposed virtual modules.

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
            path = Path(resource.real_path).resolve()
            root = Path(project.root.real_path)
            name = (
                pymodule.get_name()
                if not path.is_relative_to(root)
                else FlextInfraUtilitiesProjectDiscovery.module_name_for_file(
                    path, project_root=root, source_project=project
                )
            )
            if not name:
                msg = f"rope could not name module {resource.path}"
                raise ValueError(msg)
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
                    project=project,
                    pymodule=pymodule,
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
                if (
                    target := cls._import_law_known_prefix(
                        aliases.get(imported, imported), known
                    )
                )
                is not None
                and target != name
            )
            for name, targets in raw.items()
        }
        return graph, modules

    @classmethod
    def import_cycle_statements(
        cls,
        project: p.Infra.RopeProject,
        cycles: t.MappingKV[str, frozenset[str]],
        modules: t.MappingKV[Path, str],
    ) -> t.StrTuple:
        """Describe native top-level imports of the rejected cyclic candidate.

        Returns:
            Native statements and their one-based inclusive line ranges.

        Raises:
            ValueError: If a cyclic module is absent from its candidate view.

        """
        evidence: list[str] = []
        for path, module in sorted(modules.items()):
            if module not in cycles:
                continue
            resource = FlextInfraUtilitiesRopeCore.resolve_resource_from_path(
                project, path
            )
            if resource is None:
                message = f"cyclic candidate resource is absent: {path}"
                raise ValueError(message)
            imports = FlextInfraUtilitiesRopeCore.resolve_module_imports(
                project, resource
            )
            evidence.extend(
                f"{module}:{statement.start_line}-{statement.end_line - 1}: "
                f"{statement.import_info.get_import_statement()}"
                for statement in FlextInfraUtilitiesRopeImports.import_statements(
                    imports
                )
            )
        return tuple(evidence)

    @staticmethod
    def project_import_cycles(
        graph: t.MappingKV[str, frozenset[str]],
    ) -> t.MappingKV[str, frozenset[str]]:
        """Map each module in a runtime import cycle to its cycle's members.

        Returns:
            The resulting ``t.MappingKV[str, frozenset[str]]``.

        """
        cycles: MutableMapping[str, frozenset[str]] = {}
        for members in u.Cli.dag_strongly_connected(graph):
            if len(members) > 1:
                cycles.update(dict.fromkeys(members, members))
        return cycles

    @staticmethod
    def _import_law_known_prefix(module: str, known: frozenset[str]) -> str | None:
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


__all__: list[str] = ["FlextInfraUtilitiesImportLawGraph"]
