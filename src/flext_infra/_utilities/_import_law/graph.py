"""Runtime import graphs from the canonical captured source engine.

Bootstrap membership is a source-epoch fact. Its snapshot memo retains native
module identities and resolver roots; changed source views replace that fact.
No host import finder or package execution participates in classification.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
import inspect
import tempfile
from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path

from flext_cli import u

from flext_infra import c, e, m, p, settings, t
from flext_infra._utilities import (
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._import_law import FlextInfraUtilitiesImportLawPolicy
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeSourceBasesAliases,
)


class FlextInfraUtilitiesImportLawGraph(FlextInfraUtilitiesImportLawPolicy):
    """Read and validate the runtime graph, including requested lazy providers."""

    @classmethod
    def snapshot_bootstrap_dependencies(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        root: Path,
        namespace: str,
    ) -> frozenset[str]:
        """Derive bootstrap membership once per member's native source epoch.

        Native resource notifications replace changed parsed modules. Resolver
        roots and a fresh member inventory also participate, so restoring or
        changing a candidate view cannot reuse a different epoch's closure.

        Returns:
            The runtime dependencies reached from the publishing namespace.

        """
        root = root.resolve()
        project = snapshot.engine
        paths = FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(
            snapshot, root, project=project
        )
        resources = tuple(
            FlextInfraUtilitiesRopeRuntimeModules.file_resource_at(project, path)
            for path in paths
            if path.suffix == c.Infra.EXT_PYTHON
        )
        modules = tuple(
            FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
            for resource in resources
        )
        source_digests = tuple(
            u.Cli.sha256_bytes(project.source_bytes(Path(resource.real_path)))
            for resource in resources
        )
        source_folders = tuple(
            folder.real_path for folder in project.get_source_folders()
        )
        python_paths = tuple(
            folder.real_path for folder in project.get_python_path_folders()
        )
        previous = snapshot.bootstrap_dependencies.get(root)
        current = (namespace, source_folders, python_paths, source_digests)
        if previous is not None and cls._bootstrap_inputs_unchanged(
            previous, current, modules
        ):
            return previous.dependencies
        graph, _names = cls.persistent_import_graph(project, resources)
        if not namespace or namespace not in graph:
            return frozenset()
        dependencies = u.Cli.dag_closure(graph, frozenset({namespace})).unwrap() - {
            namespace
        }
        snapshot.bootstrap_dependencies[root] = m.Infra.WorkspaceBootstrapDependencies(
            namespace=namespace,
            modules=modules,
            source_folders=source_folders,
            python_path_folders=python_paths,
            source_digests=source_digests,
            dependencies=dependencies,
        )
        return dependencies

    @staticmethod
    def _bootstrap_inputs_unchanged(
        previous: p.Infra.WorkspaceBootstrapDependencies,
        current: tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...]],
        modules: Sequence[t.Infra.RopeSourceModule],
    ) -> bool:
        """Whether a recorded bootstrap closure was computed from these inputs.

        Returns:
            True when namespace, folders, digests and the identity of every
            resolved module equal the recorded ones.

        """
        namespace, source_folders, python_paths, source_digests = current
        return (
            previous.namespace == namespace
            and previous.source_folders == source_folders
            and previous.python_path_folders == python_paths
            and previous.source_digests == source_digests
            and all(
                old is new for old, new in zip(previous.modules, modules, strict=True)
            )
        )

    @classmethod
    def persistent_import_graph(
        cls,
        project: p.Infra.RopeProject,
        resources: Sequence[t.Infra.RopeFile],
    ) -> tuple[Mapping[str, frozenset[str]], Mapping[Path, str]]:
        """Read a live project's runtime graph, reusing unchanged module facts.

        Each module's facts are bound to its exact source bytes and the code
        that derives them, so only modules whose bytes changed are parsed
        again; the store is replaced atomically and never read partially.

        Returns:
            The same graph and module names as ``snapshot_import_graph``.

        """
        digest = hashlib.sha256(project.root.real_path.encode(c.DEFAULT_ENCODING))
        for module in (
            Path(__file__),
            Path(inspect.getfile(FlextInfraUtilitiesRopeImports)),
            Path(inspect.getfile(FlextInfraUtilitiesRopeSourceBasesAliases)),
        ):
            digest.update(module.read_bytes())
        digest.update(
            str(m.Infra.ImportGraphFacts.model_json_schema()).encode(c.DEFAULT_ENCODING)
        )
        store = settings.work_dir / "import-graphs" / f"{digest.hexdigest()}.json"
        stored: Mapping[str, p.Infra.ImportGraphModuleFacts] = (
            m.Infra.ImportGraphFacts.model_validate_json(store.read_bytes()).modules
            if store.is_file()
            else {}
        )
        known: dict[str, p.Infra.ImportGraphModuleFacts] = dict(stored)
        result = cls.snapshot_import_graph(
            project, resources=resources, module_facts=known
        )
        if known != stored:
            store.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                "wb", dir=store.parent, suffix=".tmp", delete=False
            ) as temporary:
                temporary.write(
                    m.Infra.ImportGraphFacts
                    .model_validate({"modules": known})
                    .model_dump_json()
                    .encode(c.DEFAULT_ENCODING)
                )
            Path(temporary.name).replace(store)
        return result

    @classmethod
    def snapshot_import_graph(
        cls,
        project: p.Infra.RopeProject,
        *,
        resources: Sequence[t.Infra.RopeFile] | None = None,
        module_facts: MutableMapping[str, p.Infra.ImportGraphModuleFacts] | None = None,
    ) -> tuple[Mapping[str, frozenset[str]], Mapping[Path, str]]:
        """Read runtime imports from an immutable proposed-source Rope graph.

        A live caller supplies governed resources and may pass
        ``module_facts``: a module whose name and source digest match its entry
        reuses it without a parse, and every recomputed entry replaces it.
        An authenticated candidate
        elects its complete native Python source scope before constructing
        resources; provider receipts do not enlarge that scope. An immutable
        snapshot keeps its captured inventory, including proposed virtual modules.

        Returns:
            The resulting ``tuple[Mapping[str, frozenset[str]], Mapping[Path,
                str]]``.

        Raises:
            e.OperationError: If rope could not name one module; its context
                names that module.

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
            path = Path(resource.real_path).resolve()
            root = Path(project.root.real_path)
            source = resource.read()
            pymodule = (
                None
                if path.is_relative_to(root)
                else FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
            )
            name = (
                FlextInfraUtilitiesProjectDiscovery.module_name_for_file(
                    path, project_root=root, source_project=project
                )
                if pymodule is None
                else pymodule.get_name()
            )
            if not name:
                msg = f"rope could not name module {resource.path}"
                raise e.OperationError(
                    msg, context={c.Infra.MOD_FAILURE_MODULE_KEY: str(path)}
                )
            modules[path] = name
            digest = u.Cli.sha256_bytes(source.encode(c.DEFAULT_ENCODING))
            facts = None if module_facts is None else module_facts.get(str(path))
            if facts is None or (facts.name, facts.digest) != (name, digest):
                facts = cls._module_import_facts(
                    project, resource, (name, digest, source)
                )
                if module_facts is not None:
                    module_facts[str(path)] = facts
            raw[name] = set(facts.imports)
            aliases.update({
                f"{name}.{export}": provider
                for export, provider in facts.aliases.items()
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

    @staticmethod
    def _module_import_facts(
        project: p.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        module: tuple[str, str, str],
    ) -> p.Infra.ImportGraphModuleFacts:
        """Parse one module's runtime imports and lazy export providers.

        Returns:
            The facts bound to the module's name and source digest.

        """
        name, digest, source = module
        path = Path(resource.real_path).resolve()
        package = name if path.name == c.Infra.INIT_PY else name.rpartition(".")[0]
        pymodule = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        # Requesting a lazy export loads its elected provider module. Merely
        # installing the map does not load every provider in the package.
        return m.Infra.ImportGraphModuleFacts(
            name=name,
            digest=digest,
            imports=tuple(
                sorted(
                    FlextInfraUtilitiesRopeImports.imported_module_paths(
                        FlextInfraUtilitiesRopeCore.resolve_module_imports(
                            project, resource
                        ),
                        current_package=package,
                    )
                )
            ),
            aliases=FlextInfraUtilitiesRopeSourceBasesAliases.lazy_module_aliases(
                name, path, source, project=project, pymodule=pymodule
            ),
        )

    @classmethod
    def import_cycle_statements(
        cls,
        project: p.Infra.RopeProject,
        cycles: Mapping[str, frozenset[str]],
        modules: Mapping[Path, str],
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
        graph: Mapping[str, frozenset[str]],
    ) -> Mapping[str, frozenset[str]]:
        """Map each module in a runtime import cycle to its cycle's members.

        Returns:
            The resulting ``Mapping[str, frozenset[str]]``.

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
