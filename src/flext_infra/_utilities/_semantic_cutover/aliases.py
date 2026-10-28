"""Semantic compatibility-alias cutover planning.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import ast
from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCompatibilityAliasValidation,
    FlextInfraUtilitiesProjectDiscovery,
)
from flext_infra._utilities._codemod import FlextInfraUtilitiesCodemodProject
from flext_infra._utilities._rope.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities._rope.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities._rope.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._rope.rope_runtime_types import (
    FlextInfraUtilitiesTypesRopeRuntime,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesSemanticCutoverAliasCst,
    FlextInfraUtilitiesSemanticCutoverEdits,
)


class FlextInfraUtilitiesSemanticCutoverAliases(
    FlextInfraUtilitiesSemanticCutoverAliasCst,
    FlextInfraUtilitiesSemanticCutoverEdits,
):
    """Plan atomic removal of API and locally owned service aliases."""

    @classmethod
    def _service_aliases(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
    ) -> tuple[Mapping[Path, Mapping[str, str]], Mapping[str, frozenset[str]]]:
        """Elect local declarations by native identity and upstream service lineage.

        Returns:
            The selected local aliases and their snapshot import graph.

        Raises:
            ValueError: If the upstream kernel has no native service declaration.

        """
        candidates: MutableMapping[Path, ast.ClassDef] = {}
        for path, source in cls._editable_sources(sources):
            if (
                not path.is_relative_to(workspace.repository_root)
                or path.parent.parent.name != c.Infra.DEFAULT_SRC_DIR
                or path.parent / c.Infra.INIT_PY not in sources
            ):
                continue
            declaration = cls._local_service_declaration(path, source)
            if declaration is not None:
                candidates[path] = declaration
        if not candidates:
            return {}, {}
        # Native ancestry sees the pre-rebind declaration, never a self-reference.
        ancestry_sources = dict(sources)
        for path, declaration in candidates.items():
            ancestry_sources[path] = cls._rewrite_compatibility_alias_source(
                sources[path],
                m.Infra.CompatibilityAliasRewritePlan(
                    local_aliases={"s": declaration.name},
                    import_aliases={},
                    attribute_aliases={},
                    qualified_aliases={},
                    target_bindings=frozenset(),
                ),
            )
        project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            workspace.rope_project,
            ancestry_sources,
        )
        selected: MutableMapping[Path, Mapping[str, str]] = {}
        try:
            resource = project.find_module("flext_core")
            if resource is None:
                message = "service alias retirement requires the upstream kernel source"
                raise ValueError(message)
            kernel = (
                FlextInfraUtilitiesRopeCore
                .resolve_pymodule(
                    project,
                    resource,
                )
                .get_attribute("s")
                .get_object()
            )
            if not FlextInfraUtilitiesTypesRopeRuntime.py_class(kernel):
                message = "upstream service alias has no native class declaration"
                raise ValueError(message)
            for path, declaration in candidates.items():
                value = cls._published_service_declaration(project, path, declaration)
                if value is not None and cls._inherits_service_kernel(value, kernel):
                    selected[path] = {"s": declaration.name}
            graph, _modules = FlextInfraUtilitiesCodemodProject.snapshot_import_graph(
                project
            )
        finally:
            project.close()
        return selected, graph

    @staticmethod
    def _local_service_declaration(path: Path, source: str) -> ast.ClassDef | None:
        """Find an unambiguous exported local declaration replacing the kernel alias.

        Returns:
            The local service class, or None when this is not a service alias module.

        Raises:
            ValueError: If multiple assignments compete for the service alias.

        """
        tree = ast.parse(source)
        exports = FlextInfraUtilitiesRopeAnalysis.public_export_names_source(source)
        declarations = {
            node.name: node for node in tree.body if isinstance(node, ast.ClassDef)
        }
        assignments = tuple(
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "s"
            and isinstance(node.value, ast.Name)
            and node.value.id in declarations
            and node.value.id in exports
            and "s" in exports
        )
        upstream = tuple(
            imported
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and not node.level
            and node.module == "flext_core"
            for imported in node.names
            if imported.name == "s" and imported.asname is None
        )
        if len(assignments) != 1 or len(upstream) != 1:
            return None
        rebinds = tuple(
            node
            for node in tree.body
            if isinstance(node, c.Infra.AST_ASSIGNMENT_TYPES)
            and any(
                isinstance(target, ast.Name) and target.id == "s"
                for target in (
                    node.targets if isinstance(node, ast.Assign) else (node.target,)
                )
            )
        )
        if len(rebinds) != 1:
            message = f"ambiguous service alias assignments: {path}"
            raise ValueError(message)
        return declarations[ast.unparse(assignments[0].value)]

    @staticmethod
    def _published_service_declaration(
        project: p.Infra.RopeProject,
        path: Path,
        declaration: ast.ClassDef,
    ) -> p.Infra.RopePyObject | None:
        """Authenticate a service class against its source and public namespace.

        Returns:
            The authenticated native class, or None for a non-class binding.

        Raises:
            ValueError: If the local declaration or its public export differs.

        """
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            project.get_resource(
                path.relative_to(Path(project.root.real_path)).as_posix(),
            ),
        )
        value = module.get_attribute(declaration.name).get_object()
        if not FlextInfraUtilitiesTypesRopeRuntime.py_class(value):
            return None
        provider, scope = value.get_module(), value.get_scope()
        origin = provider.get_resource()
        if (
            origin is None
            or Path(origin.real_path).resolve() != path
            or scope.get_start() != declaration.lineno
        ):
            message = f"service alias target is not its local declaration: {path}"
            raise ValueError(message)
        namespace = project.find_module(path.parent.name)
        if namespace is None or (
            FlextInfraUtilitiesRopeCore
            .resolve_pymodule(project, namespace)
            .get_attribute(declaration.name)
            .get_object()
            != value
        ):
            message = f"named service foundation is not published by its root: {path}"
            raise ValueError(message)
        return value

    @staticmethod
    def _inherits_service_kernel(
        value: p.Infra.RopePyObject, kernel: p.Infra.RopePyObject
    ) -> bool:
        """Traverse native bases without revisiting ancestry cycles.

        Returns:
            Whether the service class derives from the upstream kernel.

        """
        pending = list(FlextInfraUtilitiesDeclarationPayload.direct_bases(value))
        visited: list[p.Infra.RopePyObject] = []
        while pending:
            ancestor = pending.pop()
            if ancestor == kernel:
                return True
            if ancestor in visited:
                continue
            visited.append(ancestor)
            pending.extend(FlextInfraUtilitiesDeclarationPayload.direct_bases(ancestor))
        return False

    @staticmethod
    def _upstream_alias_reads(
        tree: ast.Module,
        aliases: Mapping[str, str],
        source: str,
    ) -> tuple[Mapping[str, str], frozenset[tuple[int, int]]]:
        """Keep eager kernel reads, not delayed reads of the later local binding.

        Returns:
            Upstream aliases and source coordinates of their eager reads.

        """
        upstream = {
            imported.asname or imported.name: f"{node.module}.{imported.name}"
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module == "flext_core"
            for imported in node.names
            if imported.name == "s" and (imported.asname or imported.name) in aliases
        }
        rebinds = {
            node.targets[0].id: node.lineno
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Name)
            and aliases.get(node.targets[0].id) == node.value.id
        }
        reads: set[tuple[int, int]] = set()
        pending: list[ast.AST] = list(tree.body)
        while pending:
            node = pending.pop()
            if isinstance(node, c.Infra.AST_CALLABLE_TYPES):
                pending.extend(node.args.defaults)
                pending.extend(
                    default for default in node.args.kw_defaults if default is not None
                )
                if not isinstance(node, ast.Lambda):
                    pending.extend(node.decorator_list)
                continue
            if (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id in upstream
                and node.id in rebinds
                and node.lineno < rebinds[node.id]
            ):
                line = source.splitlines()[node.lineno - 1]
                column = len(line.encode("utf-8")[: node.col_offset].decode("utf-8"))
                reads.add((node.lineno, column))
            pending.extend(ast.iter_child_nodes(node))
        return upstream, frozenset(reads)

    @classmethod
    def _api_alias_specs(
        cls,
        root: Path,
        findings: Sequence[m.Infra.ModOccurrence],
        service_aliases: Mapping[Path, Mapping[str, str]],
    ) -> p.Result[
        tuple[Mapping[Path, Mapping[str, str]], Mapping[str, Mapping[str, str]]]
    ]:
        """Index local aliases by declaration owner and importable namespace.

        Returns:
            The resulting ``p.Result[tuple[Mapping[Path, Mapping[str, str]],
                Mapping[str, Mapping[str, str]]]]``.

        """
        planned = r[
            tuple[Mapping[Path, Mapping[str, str]], Mapping[str, Mapping[str, str]]]
        ]
        specs_by_file: MutableMapping[Path, MutableMapping[str, str]] = {
            path: dict(aliases) for path, aliases in service_aliases.items()
        }
        specs_by_module: MutableMapping[str, MutableMapping[str, str]] = {}
        for finding in findings:
            relative = finding.file
            statement = cls._finding_statement(finding)
            if not (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
                and isinstance(statement.value, ast.Name)
            ):
                return planned.fail(
                    f"invalid compatibility-alias finding: {finding.text}",
                )
            if c.Infra.DEFAULT_SRC_DIR not in relative.parts:
                return planned.fail(f"API alias owner is outside src: {relative}")
            alias, target = statement.targets[0].id, statement.value.id
            specs_by_file.setdefault((root / relative).resolve(), {})[alias] = target
        for path, aliases in specs_by_file.items():
            relative = path.relative_to(root)
            source_index = relative.parts.index(c.Infra.DEFAULT_SRC_DIR)
            module_parts = (*relative.parts[source_index + 1 : -1], relative.stem)
            for import_module in (".".join(module_parts), module_parts[0]):
                current = specs_by_module.setdefault(import_module, {})
                for alias, target in aliases.items():
                    if current.setdefault(alias, target) != target:
                        return planned.fail(
                            f"ambiguous API alias {import_module}.{alias}"
                        )
        return planned.ok((specs_by_file, specs_by_module))

    @classmethod
    def _plan_api_aliases(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
        findings: Sequence[m.Infra.ModOccurrence],
        import_normalizer: p.Infra.SourceImportNormalizer | None,
    ) -> p.Result[tuple[m.Infra.SemanticMigrationEdit, ...]]:
        """Plan local alias removal and binding-proven consumer rewrites atomically.

        Returns:
            The resulting ``p.Result[tuple[m.Infra.SemanticMigrationEdit, ...]]``.

        """
        root = workspace.repository_root
        service_aliases, service_graph = cls._service_aliases(workspace, sources)
        specs = cls._api_alias_specs(
            root,
            tuple(
                finding for finding in findings if finding.file.name == c.Infra.API_PY
            ),
            service_aliases,
        )
        if specs.failure:
            return r[tuple[m.Infra.SemanticMigrationEdit, ...]].from_failure(specs)
        specs_by_file, specs_by_module = specs.value
        service_projects = cls._service_alias_projects(service_aliases)

        def rewrite(path: Path, source: str) -> t.Infra.TransformResult:
            local_aliases = specs_by_file.get(path, {})
            tree = ast.parse(source, filename=str(path))
            consumer_project = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
                root,
                path,
                source_project=source_project,
            )
            active_modules = cls._consumer_alias_modules(
                specs_by_module, service_projects, consumer_project
            )
            plan = cls._compatibility_alias_plan(
                path, source, tree, local_aliases, active_modules
            )
            if plan is None:
                return source, ()
            rewritten = cls._rewrite_compatibility_alias_source(
                source,
                plan,
            )
            if rewritten != source and (
                path in service_aliases
                or any(module in service_projects for module in plan.import_aliases)
            ):
                if consumer_project is None or import_normalizer is None:
                    message = (
                        "service alias consumer requires its project owner "
                        f"and import normalizer: {path}"
                    )
                    raise ValueError(message)
                normalized = import_normalizer(
                    file_path=path,
                    source=rewritten,
                    project_root=consumer_project,
                    import_graph=service_graph,
                    sources={**sources, path: rewritten},
                )
                rewritten = rewritten if normalized is None else normalized
            FlextInfraUtilitiesCompatibilityAliasValidation.require_zero_compatibility_alias_residue(
                rewritten,
                path,
                qualified_aliases=plan.qualified_aliases,
                exported_aliases=frozenset(local_aliases),
            )
            return rewritten, tuple(
                f"rewired {alias} to {target}"
                for alias, target in sorted(plan.qualified_aliases.items())
            )

        source_project = workspace.rope_project
        if service_aliases:
            return cls._semantic_edits(cls._editable_sources(sources), rewrite)
        return cls._semantic_checked_edits(cls._editable_sources(sources), rewrite)

    @classmethod
    def _compatibility_alias_plan(
        cls,
        path: Path,
        source: str,
        tree: ast.Module,
        local_aliases: Mapping[str, str],
        active_modules: Mapping[str, Mapping[str, str]],
    ) -> m.Infra.CompatibilityAliasRewritePlan | None:
        """Bind one typed alias rewrite intent before executing its CST visitor.

        Returns:
            The elected rewrite, or no intent when the module has no aliases.

        """
        import_aliases: MutableMapping[str, MutableMapping[str, str]] = {}
        attribute_aliases: MutableMapping[tuple[str, str], str] = {}
        qualified_aliases = dict(local_aliases)
        qualified_aliases.update(
            (f"{module}.{alias}", target)
            for module, aliases in active_modules.items()
            for alias, target in aliases.items()
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                selected = cls._import_from_aliases(node, active_modules)
                if selected and node.module is not None:
                    import_aliases.setdefault(node.module, {}).update(selected)
                    qualified_aliases.update(
                        (f"{node.module}.{name}", target)
                        for name, target in selected.items()
                    )
            elif isinstance(node, ast.Import):
                attribute_aliases.update(
                    ((imported.asname or imported.name, alias), target)
                    for imported in node.names
                    for alias, target in active_modules.get(imported.name, {}).items()
                )
        if not qualified_aliases:
            return None
        FlextInfraUtilitiesCompatibilityAliasValidation.require_static_compatibility_alias_exports(
            tree, path, frozenset(local_aliases)
        )
        upstream_aliases, preserved_reads = cls._upstream_alias_reads(
            tree, local_aliases, source
        )
        return m.Infra.CompatibilityAliasRewritePlan(
            local_aliases=local_aliases,
            import_aliases=import_aliases,
            attribute_aliases=attribute_aliases,
            qualified_aliases=qualified_aliases,
            target_bindings=cls._bound_names(tree),
            upstream_aliases=upstream_aliases,
            preserved_reads=preserved_reads,
        )

    @staticmethod
    def _service_alias_projects(
        service_aliases: Mapping[Path, Mapping[str, str]],
    ) -> Mapping[str, Path]:
        """Index both the declaring service module and its root namespace.

        Returns:
            The project that owns each importable service alias namespace.

        """
        return {
            module: path.parent.parent.parent
            for path in service_aliases
            for module in (f"{path.parent.name}.{path.stem}", path.parent.name)
        }

    @staticmethod
    def _consumer_alias_modules(
        modules: Mapping[str, Mapping[str, str]],
        service_projects: Mapping[str, Path],
        consumer_project: Path | None,
    ) -> Mapping[str, Mapping[str, str]]:
        """Keep local service aliases scoped to consumers in the owning project.

        Returns:
            The alias mapping visible to this consumer.

        """
        return {
            module: {
                alias: target
                for alias, target in aliases.items()
                if module not in service_projects
                or alias != "s"
                or consumer_project == service_projects[module]
            }
            for module, aliases in modules.items()
        }

    @staticmethod
    def _import_from_aliases(
        node: ast.ImportFrom, modules: Mapping[str, Mapping[str, str]]
    ) -> Mapping[str, str]:
        """Resolve explicit alias imports without accepting renamed bindings.

        Returns:
            The imported alias names and their elected targets.

        Raises:
            ValueError: If a compatibility alias import is renamed locally.

        """
        if node.module is None or node.module not in modules:
            return {}
        selected: dict[str, str] = {}
        for imported in node.names:
            target = modules[node.module].get(imported.name)
            if target is None:
                continue
            if imported.asname is not None:
                msg = (
                    "ambiguous compatibility import alias "
                    f"{imported.name} as {imported.asname}"
                )
                raise ValueError(msg)
            selected[imported.name] = target
        return selected

    @staticmethod
    def _bound_names(tree: ast.Module) -> frozenset[str]:
        """Return statically bound module names for redundant-import removal.

        Returns:
            Statically bound module names for redundant-import removal.

        """
        names: set[str] = set()
        for node in tree.body:
            if isinstance(node, c.Infra.AST_DEFINITION_TYPES):
                names.add(node.name)
            elif isinstance(node, ast.ImportFrom):
                names.update(item.asname or item.name for item in node.names)
            elif isinstance(node, ast.Import):
                names.update(
                    item.asname or item.name.split(".")[0] for item in node.names
                )
        return frozenset(names)


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverAliases"]
