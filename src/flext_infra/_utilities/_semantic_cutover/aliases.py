"""Semantic compatibility-alias cutover planning.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import MutableMapping
from pathlib import Path

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodemodProject,
    FlextInfraUtilitiesCompatibilityAliasValidation,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverAliasCst,
    FlextInfraUtilitiesSemanticCutoverEdits,
)
from flext_infra._utilities._semantic_cutover.declaration_payload import (
    FlextInfraUtilitiesDeclarationPayload,
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
        sources: t.MappingKV[Path, str],
    ) -> t.Pair[t.MappingKV[Path, t.StrMapping], t.MappingKV[str, frozenset[str]]]:
        """Elect local declarations by native identity and upstream service lineage."""
        candidates: MutableMapping[Path, ast.ClassDef] = {}
        for path, source in cls._editable_sources(sources):
            if (
                not path.is_relative_to(workspace.repository_root)
                or path.parent.parent.name != c.Infra.DEFAULT_SRC_DIR
                or path.parent / c.Infra.INIT_PY not in sources
            ):
                continue
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
            if len(assignments) == 1 and len(upstream) == 1:
                rebinds = tuple(
                    node
                    for node in tree.body
                    if isinstance(node, ast.Assign | ast.AnnAssign)
                    and any(
                        isinstance(target, ast.Name) and target.id == "s"
                        for target in (
                            node.targets
                            if isinstance(node, ast.Assign)
                            else (node.target,)
                        )
                    )
                )
                if len(rebinds) != 1:
                    message = f"ambiguous service alias assignments: {path}"
                    raise ValueError(message)
                candidates[path] = declarations[ast.unparse(assignments[0].value)]
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
        selected: MutableMapping[Path, t.StrMapping] = {}
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
            if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(kernel):
                message = "upstream service alias has no native class declaration"
                raise ValueError(message)
            for path, declaration in candidates.items():
                module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                    project,
                    project.get_resource(
                        path.relative_to(Path(project.root.real_path)).as_posix(),
                    ),
                )
                value = module.get_attribute(declaration.name).get_object()
                if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(value):
                    continue
                provider, scope = value.get_module(), value.get_scope()
                origin = None if provider is None else provider.get_resource()
                if (
                    origin is None
                    or Path(origin.real_path).resolve() != path
                    or scope is None
                    or scope.get_start() != declaration.lineno
                ):
                    message = (
                        f"service alias target is not its local declaration: {path}"
                    )
                    raise ValueError(message)
                namespace = project.find_module(path.parent.name)
                if namespace is None or (
                    FlextInfraUtilitiesRopeCore
                    .resolve_pymodule(project, namespace)
                    .get_attribute(declaration.name)
                    .get_object()
                    != value
                ):
                    message = (
                        f"named service foundation is not published by its root: {path}"
                    )
                    raise ValueError(message)
                pending = list(
                    FlextInfraUtilitiesDeclarationPayload.direct_bases(value)
                )
                visited: list[p.Infra.RopePyObject] = []
                while pending:
                    ancestor = pending.pop()
                    if ancestor == kernel:
                        selected[path] = {"s": declaration.name}
                        break
                    if ancestor in visited:
                        continue
                    visited.append(ancestor)
                    pending.extend(
                        FlextInfraUtilitiesDeclarationPayload.direct_bases(ancestor)
                    )
            graph, _modules = FlextInfraUtilitiesCodemodProject.snapshot_import_graph(
                project
            )
        finally:
            project.close()
        return selected, graph

    @staticmethod
    def _upstream_alias_reads(
        tree: ast.Module,
        aliases: t.StrMapping,
        source: str,
    ) -> t.Pair[t.StrMapping, frozenset[t.Pair[int, int]]]:
        """Keep eager kernel reads, not delayed reads of the later local binding."""
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
        reads: set[t.Pair[int, int]] = set()
        pending: list[ast.AST] = list(tree.body)
        while pending:
            node = pending.pop()
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
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
        findings: t.SequenceOf[m.Infra.ModOccurrence],
        service_aliases: t.MappingKV[Path, t.StrMapping],
    ) -> p.Result[
        t.Pair[t.MappingKV[Path, t.StrMapping], t.MappingKV[str, t.StrMapping]]
    ]:
        """Index every API alias finding by owner file and importable module.

        Returns:
            The resulting ``p.Result[t.Pair[t.MappingKV[Path, t.StrMapping],
                t.MappingKV[str, t.StrMapping]]]``.

        """
        planned = r[
            t.Pair[t.MappingKV[Path, t.StrMapping], t.MappingKV[str, t.StrMapping]]
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
        sources: t.MappingKV[Path, str],
        findings: t.SequenceOf[m.Infra.ModOccurrence],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Plan API alias removals and AST-proven consumer rewrites.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]``.

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
            return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].from_failure(specs)
        specs_by_file, specs_by_module = specs.value
        service_projects = {
            module: path.parent.parent.parent
            for path in service_aliases
            for module in (f"{path.parent.name}.{path.stem}", path.parent.name)
        }

        def rewrite(path: Path, source: str) -> t.Infra.TransformResult:
            local_aliases = specs_by_file.get(path, {})
            tree = ast.parse(source, filename=str(path))
            consumer_project = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
                root,
                path,
                source_project=workspace.rope_project,
            )
            active_modules = {
                module: {
                    alias: target
                    for alias, target in aliases.items()
                    if module not in service_projects
                    or alias != "s"
                    or consumer_project == service_projects[module]
                }
                for module, aliases in specs_by_module.items()
            }
            import_aliases: MutableMapping[str, MutableMapping[str, str]] = {}
            attribute_aliases: MutableMapping[t.Pair[str, str], str] = {}
            qualified_aliases = dict(local_aliases)
            qualified_aliases.update(
                (f"{module}.{alias}", target)
                for module, aliases in active_modules.items()
                for alias, target in aliases.items()
            )
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module is not None
                    and node.module in active_modules
                ):
                    for imported in node.names:
                        imported_target = active_modules[node.module].get(
                            imported.name,
                        )
                        if imported_target is None:
                            continue
                        if imported.asname is not None:
                            msg = (
                                "ambiguous compatibility import alias "
                                f"{imported.name} as {imported.asname}"
                            )
                            raise ValueError(msg)
                        import_aliases.setdefault(node.module, {})[imported.name] = (
                            imported_target
                        )
                        qualified_aliases[f"{node.module}.{imported.name}"] = (
                            imported_target
                        )
                elif isinstance(node, ast.Import):
                    attribute_aliases.update(
                        ((imported.asname or imported.name, alias), target)
                        for imported in node.names
                        for alias, target in active_modules.get(
                            imported.name,
                            {},
                        ).items()
                    )
            if not qualified_aliases:
                return source, ()
            FlextInfraUtilitiesCompatibilityAliasValidation.require_static_compatibility_alias_exports(
                tree,
                path,
                frozenset(local_aliases),
            )
            upstream_aliases, preserved_reads = cls._upstream_alias_reads(
                tree,
                local_aliases,
                source,
            )
            rewritten = cls._rewrite_compatibility_alias_source(
                source,
                m.Infra.CompatibilityAliasRewritePlan(
                    local_aliases=local_aliases,
                    import_aliases=import_aliases,
                    attribute_aliases=attribute_aliases,
                    qualified_aliases=qualified_aliases,
                    target_bindings=cls._bound_names(tree),
                    upstream_aliases=upstream_aliases,
                    preserved_reads=preserved_reads,
                ),
            )
            if rewritten != source and (
                path in service_aliases
                or any(module in service_projects for module in import_aliases)
            ):
                from flext_infra.refactor import FlextInfraImportNormalization

                if consumer_project is None:
                    message = f"service alias consumer has no project owner: {path}"
                    raise ValueError(message)
                normalized = FlextInfraImportNormalization.normalize_source(
                    project_root=consumer_project,
                    file_path=path,
                    source=rewritten,
                    import_graph=service_graph,
                    sources={**sources, path: rewritten},
                )
                if normalized is not None:
                    rewritten = normalized
            FlextInfraUtilitiesCompatibilityAliasValidation.require_zero_compatibility_alias_residue(
                rewritten,
                path,
                qualified_aliases=qualified_aliases,
                exported_aliases=frozenset(local_aliases),
            )
            return rewritten, tuple(
                f"rewired {alias} to {target}"
                for alias, target in sorted(qualified_aliases.items())
            )

        return cls._semantic_edits(cls._editable_sources(sources), rewrite)

    @staticmethod
    def _bound_names(tree: ast.Module) -> frozenset[str]:
        """Return statically bound module names for redundant-import removal.

        Returns:
            Statically bound module names for redundant-import removal.

        """
        names: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
                names.add(node.name)
            elif isinstance(node, ast.ImportFrom):
                names.update(item.asname or item.name for item in node.names)
            elif isinstance(node, ast.Import):
                names.update(
                    item.asname or item.name.split(".")[0] for item in node.names
                )
        return frozenset(names)


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverAliases"]
