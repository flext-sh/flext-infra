"""Immutable, identity-bound payload relocation and settings/config import rewires.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import builtins
from pathlib import Path

import libcst as cst

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCodemodProject,
    FlextInfraUtilitiesImportLaw,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesSemanticCutoverNestingCst,
    FlextInfraUtilitiesSemanticCutoverPrivateImportCst,
    FlextInfraUtilitiesSemanticNestingTypes,
)
from flext_infra._utilities._rope_source_bases_aliases import (
    FlextInfraUtilitiesRopeSourceBasesAliases,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
)
from flext_infra._utilities.protected_edit_linting import (
    FlextInfraUtilitiesProtectedEditLinting,
)


class FlextInfraUtilitiesSemanticDeclarationRelocation(
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesSemanticNestingTypes,
    FlextInfraUtilitiesSemanticCutoverNestingCst,
):
    """Relocate payloads and bind config imports to existing permitted owners."""

    @classmethod
    def _plan_declaration_relocation(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Plan every resolvable relocation; unresolved owners are findings.

        Returns:
            The edits of every declaration whose owners resolved.

        """
        edits, _findings = cls._declaration_relocation_outcome(workspace, sources)
        return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(edits)

    @classmethod
    def declaration_relocation_findings(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> t.VariadicTuple[m.Infra.DeclarationRelocationFinding]:
        """Return one finding per payload declaration whose owner is unresolved.

        Returns:
            The unresolved declarations, each naming the owner it expected.

        """
        _edits, findings = cls._declaration_relocation_outcome(workspace, sources)
        return findings

    @classmethod
    def _declaration_relocation_outcome(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> t.Pair[
        t.VariadicTuple[m.Infra.SemanticMigrationEdit],
        t.VariadicTuple[m.Infra.DeclarationRelocationFinding],
    ]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        project = runtime.snapshot_project(workspace.rope_project, sources)
        working = dict(sources)
        findings: list[m.Infra.DeclarationRelocationFinding] = []
        unresolved: set[t.Triple[Path, str, str]] = set()
        try:
            working = cls._settings_import_rewrites(project, working)
            if working != sources:
                project.close()
                project = runtime.snapshot_project(workspace.rope_project, working)
            for path in sorted(sources):
                if sources[path].startswith(c.Infra.AUTOGEN_HEADERS):
                    continue
                policy = workspace.convention(path).module_policy
                family = cls._source_family(path)
                # Tests and config/settings are not production declaration owners.
                if family is None or family == "m" or "tests" in path.parts:
                    continue
                while True:
                    candidate = cls._next_payload(
                        project,
                        path,
                        working[path],
                        unresolved,
                    )
                    if candidate is None:
                        break
                    outer, node, binding = candidate
                    declaration = f"{outer.name}.{node.name}"
                    resolved = (
                        cls._declaration_target(
                            workspace,
                            project,
                            working,
                            (path, declaration),
                        )
                        if policy.expected_family == outer.name
                        or cls._split_source_owner(project, path, outer.name, family)
                        else m.Infra.DeclarationRelocationFinding(
                            file_path=path,
                            declaration=declaration,
                            expected_owner=policy.expected_family or "<undeclared>",
                            reason=f"unresolved source owner {outer.name}",
                        )
                    )
                    if isinstance(resolved, m.Infra.DeclarationRelocationFinding):
                        findings.append(resolved)
                        unresolved.add((path, outer.name, node.name))
                        continue
                    working = cls._relocate_payload(
                        project,
                        working,
                        (path, node, binding),
                        resolved,
                    )
                    # Subsequent candidates bind to the proposed graph and coordinates.
                    project.close()
                    project = runtime.snapshot_project(workspace.rope_project, working)
            cls._preflight_declaration_graph(workspace, sources, working)
            return (
                tuple(
                    m.Infra.SemanticMigrationEdit(
                        file_path=path,
                        original_source=source,
                        updated_source=working[path],
                        changes=("relocated bound declaration/import",),
                    )
                    for path, source in sources.items()
                    if source != working[path]
                ),
                tuple(findings),
            )
        finally:
            project.close()

    @classmethod
    def _split_source_owner(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        owner: str,
        family: str,
    ) -> bool:
        """Prove a split-source owner is composed into its public family.

        Returns:
            Whether the exact authored class identity occurs in public ancestry.
        """
        directory = FlextInfraUtilitiesCodegenNamespace.facade_families()[
            family
        ].directory
        parents = [parent for parent in path.parents if parent.name == directory]
        if len(parents) != 1 or path.parent == parents[0]:
            return False
        root = Path(project.root.real_path)
        public = cls._resolve_binding(project, parents[0].parent.name, family, root, {})
        if public is None:
            return False
        declared = (
            project
            .get_pymodule(
                project.get_resource(path.relative_to(root).as_posix()),
            )
            .get_attribute(owner)
            .get_object()
        )
        return declared in cls.class_ancestry(public.get_object())

    @staticmethod
    def _source_family(path: Path) -> str | None:
        """Discover the nearest declared family directory for a source.

        Returns:
            The owning family letter, including split-source descendants.
        """
        for parent in path.parents:
            family = FlextInfraUtilitiesCodegenNamespace.facade_family_of_directory(
                parent.name,
            )
            if family is not None:
                return family
        return None

    @classmethod
    def _settings_import_rewrites(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
    ) -> t.MutableMappingKV[Path, str]:
        """Rebind config imports only to their existing, permitted declaration.

        A declaration in another family is not repaired by importing its leaf.
        Such findings require relocation and remain visible to the boundary gate.

        Returns:
            The proposed sources with config imports rebound to their
            existing, permitted declaration.

        """
        layers = FlextInfraUtilitiesImportLaw
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        root = Path(project.root.real_path)
        proposed = dict(sources)
        for path, source in sources.items():
            if source.startswith(c.Infra.AUTOGEN_HEADERS):
                continue
            located = layers.import_namespace(root, path)
            if located is None:
                continue
            namespace, _module = located
            if not cls._is_import_law_singleton(
                path, namespace, c.Infra.IMPORT_LAW_ROOT_SINGLETONS
            ):
                continue
            exports = cls._collect_settings_exports(
                (
                    project,
                    source,
                    namespace,
                    runtime,
                    root,
                    sources,
                ),
            )
            if exports:
                proposed[path] = (
                    FlextInfraUtilitiesSemanticCutoverPrivateImportCst.relocate_declared_exports(
                        source, exports
                    )
                )
        return proposed

    @staticmethod
    def _is_import_law_singleton(
        path: Path,
        namespace: Path,
        singletons: frozenset[str],
    ) -> bool:
        return any(
            part.removesuffix(".py").lstrip("_").startswith(tuple(singletons))
            for part in path.relative_to(namespace).parts
        )

    @classmethod
    def _collect_settings_exports(
        cls,
        context: tuple[
            p.Infra.RopeProject,
            str,
            Path,
            type[FlextInfraUtilitiesRopeRuntimeModules],
            Path,
            t.MappingKV[Path, str],
        ],
    ) -> t.MutableMappingKV[str, t.Pair[str, str]]:
        project, source, namespace, runtime, root, sources = context
        exports: t.MutableMappingKV[str, t.Pair[str, str]] = {}
        for statement in ast.parse(source).body:
            if not isinstance(statement, ast.ImportFrom) or statement.level:
                continue
            module_name = statement.module
            if module_name is None or module_name.split(".")[0] != namespace.name:
                continue
            for alias in statement.names:
                if alias.name == "*":
                    continue
                alias_context = (
                    project,
                    statement,
                    alias,
                    namespace,
                    runtime,
                    root,
                    sources,
                )
                resolved = cls._resolve_settings_export(alias_context)
                if resolved is not None:
                    exports[resolved[0]] = resolved[1]
        return exports

    @staticmethod
    def _resolve_settings_export(
        context: tuple[
            p.Infra.RopeProject,
            ast.ImportFrom,
            ast.alias,
            Path,
            type[FlextInfraUtilitiesRopeRuntimeModules],
            Path,
            t.MappingKV[Path, str],
        ],
    ) -> t.Pair[str, t.Pair[str, str]] | None:
        project, statement, alias, namespace, runtime, root, sources = context
        module_name = statement.module
        if module_name is None:
            return None
        binding = FlextInfraUtilitiesSemanticDeclarationRelocation._resolve_binding(
            project,
            module_name,
            alias.name,
            root,
            sources,
        )
        if binding is None:
            return None
        owner = binding.get_definition_location()[0]
        resource = owner.get_resource() if owner is not None else None
        if resource is None:
            return None
        target = Path(resource.real_path).resolve()
        if (
            target not in sources
            or not target.is_relative_to(namespace)
            or not FlextInfraUtilitiesImportLaw.import_direct_module(namespace, target)
        ):
            return None
        destination = project.get_pymodule(resource)
        declared = destination.get_attributes().get(alias.name)
        destination_name = destination.get_name()
        if (
            declared is None
            or not runtime.same_name(binding, declared)
            or destination_name == module_name
        ):
            return None
        return (
            f"{module_name}.{alias.name}",
            (destination_name, alias.name),
        )

    @staticmethod
    def _resolve_binding(
        project: p.Infra.RopeProject,
        module_name: str,
        alias_name: str,
        root: Path,
        sources: t.MappingKV[Path, str],
    ) -> p.Infra.RopePyName | None:
        provider = project.get_module(module_name)
        visited: set[str] = set()
        while (provider_resource := provider.get_resource()) is not None:
            provider_name = provider.get_name()
            if provider_name in visited:
                msg = f"declaration-relocation: cyclic lazy export {provider_name}"
                raise ValueError(msg)
            visited.add(provider_name)
            provider_path = Path(provider_resource.real_path).resolve()
            file_resource: p.Infra.RopeResource = provider_resource
            if provider_resource.is_folder():
                if not isinstance(provider_resource, p.Infra.RopeRoot):
                    msg = (
                        "declaration-relocation: invalid folder resource "
                        f"{provider_path}"
                    )
                    raise TypeError(msg)
                file_resource = provider_resource.get_child(c.Infra.INIT_PY)
                provider_path /= c.Infra.INIT_PY
            provider_file = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                file_resource,
                provider_path,
            )
            source = (
                sources[provider_path]
                if provider_path.is_relative_to(root) and provider_path in sources
                else provider_file.read()
            )
            aliases = FlextInfraUtilitiesRopeSourceBasesAliases.lazy_module_aliases(
                provider_name,
                provider_path,
                source,
            )
            route = aliases.get(alias_name)
            if route is None:
                break
            provider = project.get_module(route)
        return provider.get_attributes().get(alias_name)

    @classmethod
    def _next_payload(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        source: str,
        unresolved: set[t.Triple[Path, str, str]],
    ) -> t.Triple[ast.ClassDef, ast.ClassDef, p.Infra.RopePyName] | None:
        """Return the first bound payload declaration not already reported.

        Returns:
            The outer owner, payload node and its binding, or ``None``.

        """
        for outer in ast.parse(source).body:
            if not isinstance(outer, ast.ClassDef):
                continue
            for node in outer.body:
                if (
                    not isinstance(node, ast.ClassDef)
                    or (path, outer.name, node.name) in unresolved
                ):
                    continue
                binding = cls.payload_declaration(
                    project,
                    path,
                    f"{outer.name}.{node.name}",
                )
                if binding is not None:
                    return outer, node, binding
        return None

    @classmethod
    def _declaration_target(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
        declaration: t.Pair[Path, str],
    ) -> t.Triple[Path, str, str] | m.Infra.DeclarationRelocationFinding:
        origin, name = declaration
        root = Path(project.root.real_path)
        packages = tuple(
            parent
            for parent in origin.parents
            if (parent / c.Infra.MODELS_PY) in sources
        )
        if len(packages) != 1:
            return m.Infra.DeclarationRelocationFinding(
                file_path=origin,
                declaration=name,
                expected_owner=f"one package {c.Infra.MODELS_PY} facade",
                reason=f"unresolved model facade; found {len(packages)}",
            )
        package = packages[0]
        routes = cls._public_model_routes(project, package)
        if not routes:
            return m.Infra.DeclarationRelocationFinding(
                file_path=origin,
                declaration=name,
                expected_owner=f"lazy m export of {package / c.Infra.MODELS_PY}",
                reason=f"unresolved public lazy model export for {package}",
            )
        targets: list[t.Triple[Path, str, str]] = []
        for path, source in sources.items():
            if path.parent.parent != package or source.startswith(
                c.Infra.AUTOGEN_HEADERS,
            ):
                continue
            family = FlextInfraUtilitiesCodegenNamespace.facade_family_of_directory(
                path.parent.name,
            )
            if family is None or family != "m":
                continue
            owner = workspace.convention(path).module_policy.expected_family
            module = project.get_pymodule(
                project.get_resource(path.relative_to(root).as_posix()),
            )
            if owner is None or owner not in module.get_attributes():
                continue
            value = module.get_attribute(owner).get_object()
            for composed, route in routes:
                if value in cls.class_ancestry(composed):
                    targets.append((path, owner, route))
        targets = cls._preset_owned_targets(project, declaration, targets)
        if len(targets) != 1:
            return m.Infra.DeclarationRelocationFinding(
                file_path=origin,
                declaration=name,
                expected_owner=(
                    "one authored model owner composed into "
                    f"{package / c.Infra.MODELS_PY}"
                ),
                reason=(
                    "expected one authored composed model owner; found "
                    f"{[f'{path}:{owner}' for path, owner, _route in targets]}"
                ),
            )
        return targets[0]

    @classmethod
    def _preset_owned_targets(
        cls,
        project: p.Infra.RopeProject,
        declaration: t.Pair[Path, str],
        targets: list[t.Triple[Path, str, str]],
    ) -> list[t.Triple[Path, str, str]]:
        """Resolve local composition owners by nested preset source identity.

        Returns:
            Preset-owning candidates, or the unresolved composition candidates.
        """
        root = Path(project.root.real_path)
        outer, name = declaration[1].split(".", 1)
        bases = (
            project
            .get_pymodule(
                project.get_resource(
                    declaration[0].relative_to(root).as_posix(),
                )
            )
            .get_attribute(outer)
            .get_object()
            .get_attribute(name)
            .get_object()
            .get_superclasses()
        )
        related: list[t.Triple[Path, str, str]] = []
        for path, owner, route in targets:
            value = (
                project
                .get_pymodule(
                    project.get_resource(
                        path.relative_to(root).as_posix(),
                    )
                )
                .get_attribute(owner)
                .get_object()
            )
            # Split-source ancestry is part of the authored declaration graph.
            if any(
                child.pyobject in bases
                for ancestor in cls.class_ancestry(value)
                if (scope := ancestor.get_scope()) is not None
                for child in scope.get_scopes()
                if child.get_kind() == "Class"
            ):
                related.append((path, owner, route))
        return related or targets

    @staticmethod
    def _public_model_routes(
        project: p.Infra.RopeProject,
        package: Path,
    ) -> t.SequenceOf[t.Pair[p.Infra.RopePyObject, str]]:
        root = Path(project.root.real_path)
        facade = project.get_pymodule(
            project.get_resource(
                (package / c.Infra.MODELS_PY).relative_to(root).as_posix(),
            ),
        )
        initializer = package / c.Infra.INIT_PY
        resource = project.get_resource(initializer.relative_to(root).as_posix())
        exports = FlextInfraUtilitiesRopeSourceBasesAliases.lazy_module_aliases(
            project.get_pymodule(resource).get_name(),
            initializer,
            FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                resource,
                initializer,
            ).read(),
        )
        if exports.get("m") != facade.get_name():
            return ()
        public = facade.get_attribute("m").get_object()
        routes: list[t.Pair[p.Infra.RopePyObject, str]] = [(public, "m")]
        scope = public.get_scope()
        if scope is not None:
            routes.extend(
                (child.pyobject, f"m.{child.pyobject.get_name()}")
                for child in scope.get_scopes()
                if child.get_kind() == "Class"
            )
        return routes

    @classmethod
    def _relocate_payload(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
        declaration: t.Triple[Path, ast.ClassDef, p.Infra.RopePyName],
        destination: t.Triple[Path, str, str],
    ) -> t.MutableMappingKV[Path, str]:
        origin, node, _binding = declaration
        target, _owner, exposure = destination
        root = Path(project.root.real_path)
        facade = (
            project
            .get_pymodule(
                project.get_resource(
                    (target.parent.parent / c.Infra.MODELS_PY)
                    .relative_to(root)
                    .as_posix(),
                ),
            )
            .get_attribute("m")
            .get_object()
        )
        for segment in exposure.split(".")[1:]:
            facade = facade.get_attribute(segment).get_object()
        if node.name in facade.get_attributes():
            msg = (
                "declaration-relocation: occupied public destination "
                f"{exposure}.{node.name}"
            )
            raise ValueError(msg)
        updated = dict(sources)
        for path, source in sources.items():
            resource = project.get_resource(path.relative_to(root).as_posix())
            rewrites = cls._payload_reference_rewrites(
                project,
                resource,
                source,
                declaration,
                f"{exposure}.{node.name}",
            )
            executable = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                resource,
                source,
                rewrites,
            ).new_contents
            updated[path] = cls._import_payload_facade(
                project,
                resource,
                (source, executable),
                target,
            )
        imports, dependencies = cls._payload_imports(project, origin, target, node)
        cls._transfer_payload(
            updated,
            declaration,
            destination,
            imports,
            dependencies,
        )
        for path, source in sources.items():
            if updated[path] != source:
                updated[path] = (
                    FlextInfraUtilitiesProtectedEditLinting.remove_orphaned_imports(
                        source,
                        updated[path],
                    )
                )
        return updated

    @classmethod
    def _payload_reference_rewrites(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
        declaration: t.Triple[Path, ast.ClassDef, p.Infra.RopePyName],
        expression: str,
    ) -> t.VariadicTuple[m.Infra.SourceRewrite]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        module = project.get_pymodule(resource)
        changes: list[m.Infra.SourceRewrite] = []
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
            project,
            declaration[1].name,
            declaration[2],
            imports=True,
            in_hierarchy=False,
        )
        protected = (
            declaration[1].lineno,
            declaration[1].end_lineno or declaration[1].lineno,
        )
        for occurrence in finder.find_occurrences(resource=resource):
            if occurrence.is_defined():
                continue
            if (
                Path(resource.real_path) == declaration[0]
                and protected[0] <= occurrence.lineno <= protected[1]
            ):
                msg = "declaration-relocation: self-dependent payload"
                raise ValueError(msg)
            start, end = FlextInfraUtilitiesRopeRuntimeRefactors.word_primary_range(
                source,
                occurrence.offset,
            )
            changes.append(
                m.Infra.SourceRewrite(
                    start=start,
                    end=end,
                    text=cls._checked_type_reference(
                        runtime.scope_at(module, start),
                        expression,
                    ),
                ),
            )

        def replacement(scope: p.Infra.RopeScope, item: ast.expr) -> str | None:
            return (
                cls._checked_type_reference(scope, expression)
                if runtime.same_name(
                    declaration[2],
                    runtime.resolve_symbol(scope, item),
                )
                else None
            )

        changes.extend(
            cls._annotation_identity_rewrites(
                project,
                resource,
                source,
                (declaration[2], expression),
                protected=protected
                if Path(resource.real_path) == declaration[0]
                else None,
            ),
        )
        changes.extend(
            cls._quoted_type_rewrites(
                project,
                resource,
                source,
                replacement,
                protected=protected
                if Path(resource.real_path) == declaration[0]
                else None,
            ),
        )
        return tuple(
            {(change.start, change.end): change for change in changes}.values()
        )

    @classmethod
    def _annotation_identity_rewrites(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
        declaration: t.Pair[p.Infra.RopePyName, str],
        *,
        protected: t.Pair[int, int] | None,
    ) -> t.VariadicTuple[m.Infra.SourceRewrite]:
        """Resolve method annotations in their defining class, not execution scope.

        Returns:
            Identity-bound unquoted annotation rewrites outside the moved payload.
        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        module = project.get_pymodule(resource)
        changes: list[m.Infra.SourceRewrite] = []
        for annotation, line in cls._annotation_roots(ast.parse(source)):
            if (
                protected is not None
                and protected[0] <= annotation.lineno <= protected[1]
            ):
                continue
            start, _ = cls.expression_range(source, annotation)
            scope = runtime.scope_at(module, start, declaration_line=line)
            for item in cls._type_nodes(annotation, project, scope):
                if isinstance(item, ast.Name | ast.Attribute) and runtime.same_name(
                    declaration[0],
                    runtime.resolve_symbol(scope, item),
                ):
                    start, end = cls.expression_range(source, item)
                    changes.append(
                        m.Infra.SourceRewrite(
                            start=start,
                            end=end,
                            text=cls._checked_type_reference(scope, declaration[1]),
                        )
                    )
        return tuple(changes)

    @staticmethod
    def _import_payload_facade(
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        content: t.Pair[str, str],
        target: Path,
    ) -> str:
        if content[0] == content[1]:
            return content[0]
        if content[0].startswith(c.Infra.AUTOGEN_HEADERS):
            msg = f"declaration-relocation: generated consumer {resource.path}"
            raise ValueError(msg)
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        scope = project.get_pymodule(resource).get_scope()
        existing = scope.get_names().get("m") if scope is not None else None
        expected = project.get_pymodule(
            project.get_resource(
                (target.parent.parent / c.Infra.MODELS_PY)
                .relative_to(Path(project.root.real_path))
                .as_posix(),
            ),
        ).get_attribute("m")
        if existing is not None and not runtime.same_name(expected, existing):
            msg = (
                f"declaration-relocation: conflicting model binding in {resource.path}"
            )
            raise ValueError(msg)
        imports = runtime.module_imports_for_pymodule(
            project,
            runtime.build_string_module(project, content[1], resource=resource),
        )
        imports.add_import(
            runtime.from_import(target.parent.parent.name, 0, (("m", None),)),
        )
        return imports.get_changed_source()

    @classmethod
    def _transfer_payload(
        cls,
        updated: t.MutableMappingKV[Path, str],
        declaration: t.Triple[Path, ast.ClassDef, p.Infra.RopePyName],
        target: t.Triple[Path, str, str],
        imports: t.VariadicTuple[cst.BaseStatement],
        dependencies: t.MappingKV[str, str],
    ) -> None:
        origin, node, _binding = declaration
        moved = cst.parse_module(updated[origin])
        outer = next(
            item
            for item in moved.body
            if isinstance(item, cst.ClassDef)
            and isinstance(item.body, cst.IndentedBlock)
            and any(
                isinstance(child, cst.ClassDef) and child.name.value == node.name
                for child in item.body.body
            )
        )
        payload = next(
            child
            for child in outer.body.body
            if isinstance(child, cst.ClassDef) and child.name.value == node.name
        )
        transferred = cst.parse_statement(
            cls._dependency_source(moved.code_for_node(payload), dependencies),
        )
        kept = tuple(child for child in outer.body.body if child is not payload)
        updated[origin] = moved.with_changes(
            body=tuple(
                item.with_changes(
                    body=outer.body.with_changes(
                        body=kept or (cst.SimpleStatementLine(body=(cst.Pass(),)),),
                    ),
                )
                if item is outer
                else item
                for item in moved.body
            ),
        ).code
        destination = cst.parse_module(updated[target[0]])
        target_owner = next(
            item
            for item in destination.body
            if isinstance(item, cst.ClassDef) and item.name.value == target[1]
        )
        holder = cls._owner_holding(target_owner, (transferred,))
        if dependencies and isinstance(target_owner.body, cst.IndentedBlock):
            holder = target_owner.with_changes(
                body=target_owner.body.with_changes(
                    body=(*target_owner.body.body, transferred),
                ),
            )
        insertion = destination.body.index(target_owner)
        updated[target[0]] = destination.with_changes(
            body=(
                *destination.body[:insertion],
                *imports,
                holder,
                *destination.body[insertion + 1 :],
            ),
        ).code

    @classmethod
    def _payload_imports(
        cls,
        project: p.Infra.RopeProject,
        origin: Path,
        target: Path,
        node: ast.ClassDef,
    ) -> t.Pair[t.VariadicTuple[cst.BaseStatement], t.MappingKV[str, str]]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        root = Path(project.root.real_path)
        source = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
            project.get_resource(origin.relative_to(root).as_posix()),
            origin,
        ).read()
        destination = project.get_pymodule(
            project.get_resource(target.relative_to(root).as_posix()),
        ).get_scope()
        module = project.get_pymodule(
            project.get_resource(origin.relative_to(root).as_posix()),
        )
        scope = module.get_scope()
        if scope is None or destination is None:
            msg = (
                f"declaration-relocation: missing module scope for {origin} or {target}"
            )
            raise ValueError(msg)
        imports: t.MutableMappingKV[str, ast.Import | ast.ImportFrom] = {}
        statements = list(ast.parse(source).body)
        guard = project.get_module("typing").get_attribute("TYPE_CHECKING")
        while statements:
            statement = statements.pop(0)
            if isinstance(statement, ast.Import | ast.ImportFrom):
                for alias in statement.names:
                    imports[alias.asname or alias.name.split(".")[0]] = statement
            elif isinstance(statement, ast.If) and runtime.same_name(
                guard, runtime.resolve_symbol(scope, statement.test)
            ):
                statements[0:0] = statement.body
        dependencies, required = cls._payload_dependency_routes(
            (project, scope),
            destination,
            target,
            node,
        )
        for name in sorted(
            cls._payload_dependency_names(project, module, node, source, dependencies)
        ):
            if hasattr(builtins, name) and name not in scope.get_defined_names():
                continue
            statement = imports.get(name)
            if statement is None or (
                isinstance(statement, ast.ImportFrom) and statement.level
            ):
                msg = (
                    "declaration-relocation: unresolved/outer dependency "
                    f"{origin}:{node.name} -> {name}"
                )
                raise ValueError(msg)
            existing = destination.get_names().get(name)
            original = scope.get_names().get(name)
            if existing is not None and (
                original is None or not runtime.same_name(original, existing)
            ):
                msg = f"declaration-relocation: conflicting dependency {target}:{name}"
                raise ValueError(msg)
            if existing is None:
                aliases = [
                    alias
                    for alias in statement.names
                    if (alias.asname or alias.name.split(".")[0]) == name
                ]
                imported = (
                    ast.Import(names=aliases)
                    if isinstance(statement, ast.Import)
                    else ast.ImportFrom(module=statement.module, names=aliases, level=0)
                )
                required.append(cst.parse_statement(ast.unparse(imported) + "\n"))
        return tuple(required), dependencies

    @staticmethod
    def _dependency_source(source: str, dependencies: t.MappingKV[str, str]) -> str:
        """Rewrite only bound executable attributes, retaining ordinary strings.

        Returns:
            Source rebound to the resolved dependency owners.
        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        rewrites = sorted(
            (
                runtime.source_offset(source, item),
                len(ast.get_source_segment(source, item) or ""),
                dependencies[ast.unparse(item)],
            )
            for item in ast.walk(ast.parse(source))
            if isinstance(item, ast.Attribute) and ast.unparse(item) in dependencies
        )
        end = -1
        selected: list[t.Triple[int, int, str]] = []
        for start, length, replacement in sorted(
            rewrites, key=lambda row: (row[0], -row[1])
        ):
            if start >= end:
                selected.append((start, length, replacement))
                end = start + length
        for start, length, replacement in reversed(selected):
            source = source[:start] + replacement + source[start + length :]
        return source

    @classmethod
    def _payload_dependency_names(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        node: ast.ClassDef,
        source: str,
        dependencies: t.MappingKV[str, str],
    ) -> set[str]:
        """Keep original imports only when transferred code still loads them.

        Returns:
            The unreplaced original dependency roots.
        """
        remaining = {
            item.id
            for item in ast.walk(
                ast.parse(cls._dependency_source(ast.unparse(node), dependencies))
            )
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
        }
        return cls._payload_loaded_names(project, module, node, source) - (
            {expression.split(".")[0] for expression in dependencies} - remaining
        )

    @classmethod
    def _payload_dependency_routes(
        cls,
        context: t.Pair[p.Infra.RopeProject, p.Infra.RopeScope],
        destination: p.Infra.RopeScope,
        target: Path,
        node: ast.ClassDef,
    ) -> t.Pair[t.MappingKV[str, str], list[cst.BaseStatement]]:
        """Resolve nested dependencies to their authored declaration identities.

        Returns:
            Attribute replacements and required direct owner imports.

        Raises:
            ValueError: If a direct owner name conflicts with a destination binding.
        """
        dependencies: t.MutableMappingKV[str, str] = {}
        imports: t.MutableMappingKV[str, cst.BaseStatement] = {}
        for item in ast.walk(node):
            if not isinstance(item, ast.Attribute):
                continue
            owner = cls._payload_dependency_owner(context, item, target)
            if owner is None:
                continue
            provider, outer, child = owner
            resource = provider.get_resource()
            if resource is not None and Path(resource.real_path).resolve() == target:
                replacement = child
            else:
                existing = destination.get_names().get(outer)
                declared = provider.get_attribute(outer)
                if (
                    existing is not None
                    and not FlextInfraUtilitiesRopeRuntimeModules.same_name(
                        existing, declared
                    )
                ):
                    msg = (
                        "declaration-relocation: conflicting dependency "
                        f"{target}:{outer}"
                    )
                    raise ValueError(msg)
                if existing is None:
                    imports[outer] = cst.parse_statement(
                        f"from {provider.get_name()} import {outer}\n",
                    )
                replacement = f"{outer}.{child}"
            dependencies[ast.unparse(item)] = replacement
        return dependencies, list(imports.values())

    @classmethod
    def _payload_dependency_owner(
        cls,
        context: t.Pair[p.Infra.RopeProject, p.Infra.RopeScope],
        item: ast.Attribute,
        target: Path,
    ) -> t.Triple[p.Infra.RopePyModule, str, str] | None:
        """Find a unique same-package nested declaration, never a facade alias.

        Returns:
            The declaring module, outer class and nested declaration, if unique.
        """
        project, scope = context
        segments = ast.unparse(item).split(".")
        imported = scope.get_names().get(segments[0])
        if (
            isinstance(imported, p.Infra.RopeImportedName)
            and imported.imported_module.module_name is not None
            and not imported.imported_module.level
        ):
            binding = cls._resolve_binding(
                project,
                imported.imported_module.module_name,
                imported.imported_name,
                Path(project.root.real_path),
                {},
            )
            if binding is not None and isinstance(item.value, ast.Name):
                owned = cls._composed_dependency_owner(
                    binding.get_object(), segments[1], target
                )
                if owned is not None:
                    return owned
            for segment in segments[1:]:
                if binding is None:
                    break
                binding = binding.get_object().get_attributes().get(segment)
        else:
            binding = FlextInfraUtilitiesRopeRuntimeModules.resolve_symbol(scope, item)
        if binding is None:
            return None
        provider, line = binding.get_definition_location()
        if provider is None or line is None:
            return None
        resource = provider.get_resource()
        if (
            resource is None
            or Path(resource.real_path).resolve().parent.parent != target.parent.parent
        ):
            return None
        owners = [
            (outer, child)
            for outer in ast.parse(provider.source_code).body
            if isinstance(outer, ast.ClassDef)
            for child in outer.body
            if isinstance(child, ast.ClassDef) and child.lineno == line
        ]
        return (
            (provider, owners[0][0].name, owners[0][1].name)
            if len(owners) == 1
            else None
        )

    @classmethod
    def _composed_dependency_owner(
        cls,
        composed: p.Infra.RopePyObject,
        name: str,
        target: Path,
    ) -> t.Triple[p.Infra.RopePyModule, str, str] | None:
        """Bind preset and primitive exports to the class that declares them.

        Returns:
            The unique authored declaring owner, including assigned primitives.

        Raises:
            ValueError: If multiple authored owners declare the dependency.
        """
        owners: list[t.Triple[p.Infra.RopePyModule, str, str]] = []
        for ancestor in cls.class_ancestry(composed):
            scope = ancestor.get_scope()
            provider = ancestor.get_module()
            resource = provider.get_resource() if provider is not None else None
            if scope is None or provider is None or resource is None:
                continue
            path = Path(resource.real_path).resolve()
            if (
                path.parent.parent == target.parent.parent
                and name in scope.get_defined_names()
            ):
                owners.append((provider, ancestor.get_name(), name))
        if len(owners) > 1:
            msg = f"declaration-relocation: ambiguous dependency owner {name}"
            raise ValueError(msg)
        return owners[0] if owners else None

    @classmethod
    def _payload_loaded_names(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        node: ast.ClassDef,
        source: str,
    ) -> set[str]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        bound = {
            parameter.name
            for parameter in node.type_params
            if isinstance(parameter, ast.TypeVar | ast.ParamSpec | ast.TypeVarTuple)
        } | {
            statement.target.id
            for statement in node.body
            if isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
        }
        methods = tuple(
            statement
            for statement in node.body
            if isinstance(statement, ast.FunctionDef)
        )
        method_nodes = {item for method in methods for item in ast.walk(method)}
        loaded = {
            item.id
            for item in ast.walk(node)
            if item not in method_nodes
            and isinstance(item, ast.Name)
            and isinstance(item.ctx, ast.Load)
        } - bound
        for method in methods:
            loaded.update(cls._method_loaded_names(method))

        def quoted_names(annotation: ast.expr, lexical: p.Infra.RopeScope) -> set[str]:
            found: set[str] = set()
            for item in cls._type_nodes(annotation, project, lexical):
                if isinstance(item, ast.Name):
                    found.add(item.id)
                elif isinstance(item, ast.Constant) and isinstance(item.value, str):
                    found.update(
                        quoted_names(ast.parse(item.value, mode="eval").body, lexical),
                    )
            return found

        for annotation, declaration_line in cls._annotation_roots(
            ast.Module(body=[node], type_ignores=[]),
        ):
            lexical = runtime.scope_at(
                module,
                runtime.source_offset(source, annotation),
                declaration_line=declaration_line,
            )
            loaded.update(quoted_names(annotation, lexical) - bound)
        return loaded

    @staticmethod
    def _method_loaded_names(method: ast.FunctionDef) -> set[str]:
        if any(
            item is not method
            and isinstance(
                item,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Lambda,
                    ast.ListComp,
                    ast.SetComp,
                    ast.DictComp,
                    ast.GeneratorExp,
                ),
            )
            for item in ast.walk(method)
        ):
            msg = "declaration-relocation: unproven nested validator scope"
            raise ValueError(msg)
        arguments = (
            *method.args.posonlyargs,
            *method.args.args,
            *method.args.kwonlyargs,
            method.args.vararg,
            method.args.kwarg,
        )
        locals_ = {argument.arg for argument in arguments if argument is not None} | {
            item.id
            for item in ast.walk(method)
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store)
        }
        return {
            item.id
            for item in ast.walk(method)
            if isinstance(item, ast.Name)
            and isinstance(item.ctx, ast.Load)
            and item.id not in locals_
        }

    @classmethod
    def preflight_semantic_import_graph(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        original: t.MappingKV[Path, str],
        proposed: t.MappingKV[Path, str],
    ) -> None:
        """Expose the existing graph guard for a composed semantic candidate."""
        cls._preflight_declaration_graph(workspace, original, proposed)

    @staticmethod
    def _preflight_declaration_graph(
        workspace: p.Infra.RopeWorkspaceDsl,
        original: t.MappingKV[Path, str],
        proposed: t.MappingKV[Path, str],
    ) -> None:
        """Reject new runtime cycles in the proposed immutable import graph.

        Raises:
            ValueError: If declaration-relocation.
        """
        before = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            workspace.rope_project,
            original,
        )
        after = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            workspace.rope_project,
            proposed,
        )
        try:
            old, _ = FlextInfraUtilitiesCodemodProject.snapshot_import_graph(before)
            new, _ = FlextInfraUtilitiesCodemodProject.snapshot_import_graph(after)
            cycles = FlextInfraUtilitiesCodemodProject.project_import_cycles(new)
            baseline = FlextInfraUtilitiesCodemodProject.project_import_cycles(old)
            introduced = {
                name: members
                for name, members in cycles.items()
                if baseline.get(name) != members
            }
            if introduced:
                edges = {
                    name: sorted(new[name] & members)
                    for name, members in introduced.items()
                }
                msg = (
                    "declaration-relocation: proposed runtime import cycle; "
                    f"nothing published: {edges}"
                )
                raise ValueError(msg)
        finally:
            before.close()
            after.close()


__all__: list[str] = ["FlextInfraUtilitiesSemanticDeclarationRelocation"]
