"""Immutable, identity-bound payload relocation and settings/config import rewires.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import builtins
from pathlib import Path
from textwrap import dedent, indent

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCodemodProject,
    FlextInfraUtilitiesImportLaw,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeStructure,
)
from flext_infra._utilities._rope_source_bases_aliases import (
    FlextInfraUtilitiesRopeSourceBasesAliases,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)

_COMPOSED_REFERENCE_SEGMENTS = 2


class FlextInfraUtilitiesSemanticDeclarationRelocation(
    FlextInfraUtilitiesDeclarationPayload,
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
        project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            workspace.rope_project, sources
        )
        working = dict(sources)
        findings: list[m.Infra.DeclarationRelocationFinding] = []
        unresolved: set[t.Triple[Path, str, str]] = set()
        try:
            working, import_findings = cls._declaration_import_rewrites(
                project, working
            )
            findings.extend(import_findings)
            if working != sources:
                project.close()
                project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                    workspace.rope_project, working
                )
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
                    outer_name = outer.pyobject.get_name()
                    node_name = node.pyobject.get_name()
                    declaration = f"{outer_name}.{node_name}"
                    resolved = (
                        cls._declaration_target(
                            workspace,
                            project,
                            working,
                            (path, declaration),
                        )
                        if policy.expected_family == outer_name
                        or cls._split_source_owner(project, path, outer_name, family)
                        else m.Infra.DeclarationRelocationFinding(
                            file_path=path,
                            declaration=declaration,
                            expected_owner=policy.expected_family or "<undeclared>",
                            reason=f"unresolved source owner {outer_name}",
                        )
                    )
                    if isinstance(resolved, m.Infra.DeclarationRelocationFinding):
                        findings.append(resolved)
                        unresolved.add((path, outer_name, node_name))
                        continue
                    working = cls._relocate_payload(
                        project,
                        working,
                        (path, node, binding),
                        resolved,
                    )
                    # Subsequent candidates bind to the proposed graph and coordinates.
                    project.close()
                    project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                        workspace.rope_project, working
                    )
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
    def _declaration_import_rewrites(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
    ) -> t.Pair[
        t.MutableMappingKV[Path, str],
        t.VariadicTuple[m.Infra.DeclarationRelocationFinding],
    ]:
        """Rebind declarations only to identity-proven external public exports.

        An own-namespace provider has to relocate; importing its defining leaf
        does not repair the dependency. Unresolved identities remain typed red
        findings while the other safe semantic edits can proceed.

        Returns:
            Proposed sources and every dependency lacking a permitted owner.

        """
        layers = FlextInfraUtilitiesImportLaw
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        root = Path(project.root.real_path)
        proposed = dict(sources)
        findings: list[m.Infra.DeclarationRelocationFinding] = []
        for path, source in sources.items():
            if source.startswith(c.Infra.AUTOGEN_HEADERS):
                continue
            located = layers.import_namespace(root, path)
            if located is None:
                continue
            namespace, module = located
            if layers.import_module_role(module) != "layer0":
                continue
            exports = cls._collect_settings_exports(
                (
                    project,
                    path,
                    source,
                    namespace,
                    runtime,
                    root,
                    sources,
                ),
                findings,
            )
            if exports:
                proposed[path] = cls._relocate_settings_exports(
                    project,
                    path,
                    source,
                    exports,
                )
        return proposed, tuple(findings)

    @classmethod
    def _collect_settings_exports(
        cls,
        context: tuple[
            p.Infra.RopeProject,
            Path,
            str,
            Path,
            type[FlextInfraUtilitiesRopeRuntimeModules],
            Path,
            t.MappingKV[Path, str],
        ],
        findings: list[m.Infra.DeclarationRelocationFinding],
    ) -> t.MutableMappingKV[str, t.Pair[str, str]]:
        project, path, _source, namespace, runtime, root, sources = context
        exports: t.MutableMappingKV[str, t.Pair[str, str]] = {}
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            project.get_resource(path.relative_to(root).as_posix()),
        )
        for statement in runtime.module_imports_for_pymodule(project, module).imports:
            information = statement.import_info
            if not isinstance(information, p.Infra.RopeFromImport) or information.level:
                continue
            module_name = information.module_name
            if module_name.split(".")[0] != namespace.name:
                continue
            for name, _alias in information.names_and_aliases:
                if name == "*":
                    continue
                alias_context = (
                    project,
                    module_name,
                    name,
                    namespace,
                    runtime,
                    root,
                    sources,
                )
                resolved = cls._resolve_settings_export(alias_context)
                if resolved is not None:
                    exports[resolved[0]] = resolved[1]
                else:
                    findings.append(
                        m.Infra.DeclarationRelocationFinding(
                            file_path=path,
                            declaration=f"{module_name}.{name}",
                            expected_owner="external public declaration",
                            reason=(
                                "own-namespace dependency has no "
                                "identity-proven external export"
                            ),
                        )
                    )
        return exports

    @staticmethod
    def _resolve_settings_export(
        context: tuple[
            p.Infra.RopeProject,
            str,
            str,
            Path,
            type[FlextInfraUtilitiesRopeRuntimeModules],
            Path,
            t.MappingKV[Path, str],
        ],
    ) -> t.Pair[str, t.Pair[str, str]] | None:
        project, module_name, name, namespace, runtime, root, sources = context
        binding = FlextInfraUtilitiesSemanticDeclarationRelocation._resolve_binding(
            project,
            module_name,
            name,
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
        if target.is_relative_to(namespace):
            return None
        destination = project.get_pymodule(resource)
        destination_name = destination.get_name().split(".")[0]
        declared = FlextInfraUtilitiesSemanticDeclarationRelocation._resolve_binding(
            project,
            destination_name,
            name,
            root,
            sources,
        )
        if (
            declared is None
            or not runtime.same_name(binding, declared)
            or destination_name == module_name
        ):
            return None
        return (
            f"{module_name}.{name}",
            (destination_name, name),
        )

    @classmethod
    def _relocate_settings_exports(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        source: str,
        exports: t.MappingKV[str, t.Pair[str, str]],
    ) -> str:
        """Rebind native import records while retaining their lexical aliases.

        Returns:
            The rewritten source text with rebound import records.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        resource = project.get_resource(
            path.relative_to(Path(project.root.real_path)).as_posix(),
        )
        imports = runtime.module_imports_for_pymodule(
            project,
            FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource),
        )
        rewrites: list[m.Infra.SourceRewrite] = []
        lines = cls._source_lines(source)
        for statement in imports.imports:
            information = statement.import_info
            if not isinstance(information, p.Infra.RopeFromImport):
                continue
            grouped: dict[str, list[t.Pair[str, str | None]]] = {}
            changed = False
            for name, alias in information.names_and_aliases:
                destination = exports.get(f"{information.module_name}.{name}")
                bound_alias = alias
                if destination is None:
                    destination = (information.module_name, name)
                else:
                    changed = True
                    bound_alias = alias or (name if destination[1] != name else None)
                grouped.setdefault(destination[0], []).append((
                    destination[1],
                    bound_alias,
                ))
            if not changed:
                continue
            start = lines.get_line_start(statement.start_line)
            end = min(lines.get_line_start(statement.end_line), len(source))
            rewrites.append(
                m.Infra.SourceRewrite(
                    start=start,
                    end=end,
                    text="\n".join(
                        runtime.from_import(
                            module, information.level, tuple(names)
                        ).get_import_statement()
                        for module, names in grouped.items()
                    )
                    + "\n",
                ),
            )
        return FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource,
            source,
            tuple(rewrites),
        ).new_contents

    @staticmethod
    def _source_lines(source: str) -> p.Infra.RopeSourceLines:
        lines = FlextInfraUtilitiesRopeRuntimeRefactors.runtime_callable(
            "rope.base.codeanalyze",
            "SourceLinesAdapter",
        )(source)
        if not isinstance(lines, p.Infra.RopeSourceLines):
            msg = "declaration-relocation: missing native source lines"
            raise TypeError(msg)
        return lines

    @staticmethod
    def _provider_file(
        provider_resource: p.Infra.RopeResource,
    ) -> t.Pair[Path, t.Infra.RopeFile]:
        """Resolve a provider resource to its physical module file.

        A package resolves to its initializer.

        Returns:
            The provider module path and its file resource.

        Raises:
            TypeError: If a folder resource is not a Rope root.

        """
        provider_path = Path(provider_resource.real_path).resolve()
        file_resource: p.Infra.RopeResource = provider_resource
        if provider_resource.is_folder():
            if not isinstance(provider_resource, p.Infra.RopeRoot):
                msg = f"declaration-relocation: invalid folder resource {provider_path}"
                raise TypeError(msg)
            file_resource = provider_resource.get_child(c.Infra.INIT_PY)
            provider_path /= c.Infra.INIT_PY
        return provider_path, FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
            file_resource,
            provider_path,
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
        while FlextInfraUtilitiesRopeRuntimeTypes.semantic_module(provider):
            provider_resource = provider.get_resource()
            if provider_resource is None:
                break
            provider_name = provider.get_name()
            if provider_name in visited:
                msg = f"declaration-relocation: cyclic lazy export {provider_name}"
                raise ValueError(msg)
            visited.add(provider_name)
            provider_path, provider_file = (
                FlextInfraUtilitiesSemanticDeclarationRelocation._provider_file(
                    provider_resource,
                )
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
                project=project,
                pymodule=provider,
            )
            route = aliases.get(alias_name)
            if route is None:
                break
            provider = project.get_module(route)
        else:
            message = "declaration provider has no native semantic module"
            raise TypeError(message)
        return provider.get_attributes().get(alias_name)

    @classmethod
    def _next_payload(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        _source: str,
        unresolved: set[t.Triple[Path, str, str]],
    ) -> t.Triple[p.Infra.RopeScope, p.Infra.RopeScope, p.Infra.RopePyName] | None:
        """Return the first bound payload declaration not already reported.

        Returns:
            The outer owner, payload node and its binding, or ``None``.

        """
        root = Path(project.root.real_path)
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            project.get_resource(path.relative_to(root).as_posix()),
        )
        module_scope = module.get_scope()
        for outer in module_scope.get_scopes():
            if outer.get_kind() != "Class":
                continue
            for node in outer.get_scopes():
                outer_name = outer.pyobject.get_name()
                node_name = node.pyobject.get_name()
                if (
                    node.get_kind() != "Class"
                    or (path, outer_name, node_name) in unresolved
                ):
                    continue
                binding = cls.payload_declaration(
                    project,
                    path,
                    f"{outer_name}.{node_name}",
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
        declared = (
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
        )
        bases = cls.direct_bases(declared)
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
            project=project,
            pymodule=project.get_pymodule(resource),
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

    @staticmethod
    def _checked_payload_facade(
        project: p.Infra.RopeProject,
        target: Path,
        exposure: str,
        name: str,
    ) -> p.Infra.RopePyObject:
        """Resolve the destination facade object and reject occupied names.

        Args:
            project: The Rope project owning the cutover sources.
            target: Destination module path of the relocated declaration.
            exposure: Public facade exposure path below the ``m`` namespace.
            name: Public name the relocated declaration will occupy.

        Returns:
            The facade object at the destination exposure path.

        Raises:
            ValueError: If the destination name is already occupied publicly.

        """
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
        if name in facade.get_attributes():
            msg = (
                f"declaration-relocation: occupied public destination {exposure}.{name}"
            )
            raise ValueError(msg)
        return facade

    @classmethod
    def _relocate_payload(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
        declaration: t.Triple[Path, p.Infra.RopeScope, p.Infra.RopePyName],
        destination: t.Triple[Path, str, str],
    ) -> t.MutableMappingKV[Path, str]:
        origin, node, _binding = declaration
        name = node.pyobject.get_name()
        target, _owner, exposure = destination
        root = Path(project.root.real_path)
        cls._checked_payload_facade(project, target, exposure, name)
        updated = dict(sources)
        for path, source in sources.items():
            resource = project.get_resource(path.relative_to(root).as_posix())
            rewrites = cls._payload_reference_rewrites(
                project,
                resource,
                source,
                declaration,
                f"{exposure}.{name}",
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
        transplanted = cls._payload_transplant(
            project,
            updated,
            declaration,
            dependencies,
        )
        cls._payload_insert(project, updated, destination, imports, transplanted)
        for path, source in sources.items():
            if updated[path] != source:
                updated[path] = cls._remove_orphaned_imports(
                    project,
                    project.get_resource(path.relative_to(root).as_posix()),
                    source,
                    updated[path],
                )
        return updated

    @classmethod
    def _remove_orphaned_imports(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        original: str,
        proposed: str,
    ) -> str:
        """Remove only native imports whose last proven use this cutover removed.

        Args:
            project: The Rope project owning the cutover sources.
            resource: Source resource of the rewritten module.
            original: Source text before this cutover's rewrites.
            proposed: Source text after this cutover's rewrites.

        Returns:
            The proposed text with newly orphaned imports removed.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        before = runtime.build_string_module(project, original, resource=resource)
        after = runtime.build_string_module(project, proposed, resource=resource)
        orphaned = cls._used_import_names(project, before) - cls._used_import_names(
            project,
            after,
        )
        if not orphaned:
            return proposed
        rewrites: list[m.Infra.SourceRewrite] = []
        lines = cls._source_lines(proposed)
        for statement in runtime.module_imports_for_pymodule(project, after).imports:
            information = statement.import_info
            retained = tuple(
                (name, alias)
                for name, alias in information.names_and_aliases
                if (alias or name.partition(".")[0]) not in orphaned
            )
            if retained == tuple(information.names_and_aliases):
                continue
            replacement = (
                runtime.from_import(
                    information.module_name,
                    information.level,
                    retained,
                )
                if isinstance(information, p.Infra.RopeFromImport)
                else runtime.normal_import(retained)
            )
            rewrites.append(
                m.Infra.SourceRewrite(
                    start=lines.get_line_start(statement.start_line),
                    end=min(lines.get_line_start(statement.end_line), len(proposed)),
                    text=replacement.get_import_statement() + "\n" if retained else "",
                ),
            )
        return FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource,
            proposed,
            tuple(rewrites),
        ).new_contents

    @classmethod
    def _used_import_names(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
    ) -> set[str]:
        imports = cls.native_import_infos(project, module)
        names = {
            alias or name.partition(".")[0]
            for information in imports
            for name, alias in information.names_and_aliases
        }
        used: set[str] = set()
        for name in names:
            binding = module.get_scope().get_names().get(name)
            if binding is None:
                continue
            finder = FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
                project,
                name,
                binding,
                imports=False,
                in_hierarchy=False,
            )
            if any(
                not occurrence.is_defined()
                for occurrence in finder.find_occurrences(pymodule=module)
            ):
                used.add(name)
        types = FlextInfraUtilitiesSemanticFamilyTypeReferences
        for _begin, _end, literal, scope in types.quoted_type_regions(
            module.source_code,
            project,
            module,
        ):
            used.update(cls._quoted_dependency_names(project, scope, literal) & names)
        exported = tuple(
            statement
            for statement in FlextInfraUtilitiesRopeStructure.logical_statements(
                module.source_code
            )
            if FlextInfraUtilitiesRopeStructure.target_name(statement) == "__all__"
        )
        for (
            start,
            stop,
            _metadata,
        ) in FlextInfraUtilitiesRopeRuntimeRefactors.ignored_regions(
            module.source_code
        ):
            if module.source_code[start] == "#" or not any(
                statement.start_offset <= start < stop <= statement.end_offset
                for statement in exported
            ):
                continue
            literal = types.string_constant(module.source_code[start:stop])
            if literal in names:
                used.add(literal)
        return used

    @classmethod
    def _payload_reference_rewrites(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
        declaration: t.Triple[Path, p.Infra.RopeScope, p.Infra.RopePyName],
        expression: str,
    ) -> t.VariadicTuple[m.Infra.SourceRewrite]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                resource, resource.path
            ),
        )
        changes: list[m.Infra.SourceRewrite] = []
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
            project,
            declaration[1].pyobject.get_name(),
            declaration[2],
            imports=True,
            in_hierarchy=False,
        )
        protected = (
            declaration[1].get_start(),
            declaration[1].get_end(),
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
                    text=cls._checked_relocation_reference(
                        runtime.scope_at(module, start),
                        expression,
                    ),
                ),
            )

        changes.extend(
            cls._type_identity_rewrites(
                project,
                resource,
                source,
                (declaration[2], expression),
                protected=protected
                if Path(resource.real_path) == declaration[0]
                else None,
            ),
        )
        return tuple(
            {(change.start, change.end): change for change in changes}.values()
        )

    @classmethod
    def _checked_relocation_reference(
        cls, scope: p.Infra.RopeScope, expression: str
    ) -> str:
        root = expression.partition(".")[0]
        if not all(part.isidentifier() for part in expression.split(".")):
            msg = f"quoted type destination is not an identifier chain: {expression}"
            raise TypeError(msg)
        current = scope
        while current.parent is not None:
            if root in current.get_defined_names():
                msg = f"shadowed quoted type destination: {expression}"
                raise ValueError(msg)
            current = current.parent
        return expression

    @classmethod
    def _type_identity_rewrites(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
        identity: t.Pair[p.Infra.RopePyName, str],
        *,
        protected: t.Pair[int, int] | None,
    ) -> t.VariadicTuple[m.Infra.SourceRewrite]:
        binding, expression = identity
        types = FlextInfraUtilitiesSemanticFamilyTypeReferences
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                resource, resource.path
            ),
        )
        lines = cls._source_lines(source)
        edits: list[m.Infra.SourceRewrite] = []

        def replace(lexical: p.Infra.RopeScope, value: str) -> str | None:
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            return (
                cls._checked_relocation_reference(lexical, expression)
                if runtime.same_name(binding, runtime.expression_name(lexical, value))
                else None
            )

        runtime = FlextInfraUtilitiesRopeRuntimeModules
        for begin, end, line in types.annotation_regions(source, module):
            if protected is not None and (
                protected[0] <= lines.get_line_number(begin) <= protected[1]
            ):
                continue
            scope = runtime.scope_at(module, begin, declaration_line=line)
            for first, last in types.reference_regions(source[begin:end]):
                start, stop = begin + first, begin + last
                changed = replace(scope, source[start:stop])
                if changed is not None:
                    edits.append(
                        m.Infra.SourceRewrite(start=start, end=stop, text=changed)
                    )
        for begin, end, literal, scope in types.quoted_type_regions(
            source,
            project,
            module,
        ):
            if protected is not None and (
                protected[0] <= lines.get_line_number(begin) <= protected[1]
            ):
                continue
            updated = types.rewrite_type_source(literal, project, scope, replace)
            if updated != literal:
                edits.append(
                    m.Infra.SourceRewrite(start=begin, end=end, text=repr(updated)),
                )
        return tuple(edits)

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
        scope = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project, resource
        ).get_scope()
        existing = scope.get_names().get("m")
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
    def _payload_transplant(
        cls,
        project: p.Infra.RopeProject,
        updated: t.MutableMappingKV[Path, str],
        declaration: t.Triple[Path, p.Infra.RopeScope, p.Infra.RopePyName],
        dependencies: t.MappingKV[t.Pair[int, int], str],
    ) -> t.Pair[str, str]:
        """Cut the payload body out of its origin and return its text.

        Args:
            project: The Rope project owning the cutover sources.
            updated: Mutable source map mutated in place for the origin file.
            declaration: Origin path, payload scope, and binding triple.
            dependencies: Attribute replacements applied to the payload body.

        Returns:
            The dedented payload text and its original indentation.

        Raises:
            TypeError: A payload or its enclosing declaration lacks a source scope.

        """
        origin, node, _binding = declaration
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        origin_module = runtime.build_string_module(
            project,
            updated[origin],
            resource=project.get_resource(
                origin.relative_to(Path(project.root.real_path)).as_posix(),
            ),
        )
        if node.parent is None:
            message = "payload declaration has no enclosing source scope"
            raise TypeError(message)
        outer_name = node.parent.pyobject.get_name()
        outer = origin_module.get_attribute(outer_name).get_object().get_scope()
        if outer is None:
            message = "payload enclosing declaration has no native source scope"
            raise TypeError(message)
        payload = (
            outer.pyobject
            .get_attribute(node.pyobject.get_name())
            .get_object()
            .get_scope()
        )
        if payload is None:
            message = "payload declaration has no native source scope"
            raise TypeError(message)
        lines = cls._source_lines(updated[origin])
        start = lines.get_line_start(payload.get_start())
        end = min(lines.get_line_end(payload.get_end()) + 1, len(updated[origin]))
        transferred = dedent(
            cls._dependency_source(
                updated[origin][start:end],
                dependencies,
            )
        )
        body_statements = tuple(
            statement
            for statement in FlextInfraUtilitiesRopeStructure.logical_statements(
                updated[origin]
            )
            if outer.get_start() < statement.line <= outer.get_end()
            and not start <= statement.start_offset < end
        )
        indentation = lines.get_line(payload.get_start())[
            : len(lines.get_line(payload.get_start()))
            - len(lines.get_line(payload.get_start()).lstrip())
        ]
        updated[origin] = (
            updated[origin][:start]
            + ("" if body_statements else indentation + "pass\n")
            + updated[origin][end:]
        )
        return transferred, indentation

    @classmethod
    def _payload_insert(
        cls,
        project: p.Infra.RopeProject,
        updated: t.MutableMappingKV[Path, str],
        target: t.Triple[Path, str, str],
        imports: t.VariadicTuple[p.Infra.RopeImportInfo],
        transplanted: t.Pair[str, str],
    ) -> None:
        """Insert the transplanted payload into its destination owner scope.

        Args:
            project: The Rope project owning the cutover sources.
            updated: Mutable source map mutated in place for the target file.
            target: Destination path, owner name, and exposure triple.
            imports: Required imports added to the destination module.
            transplanted: Payload text and indentation from the origin cut.

        Raises:
            TypeError: The destination owner lacks its native source scope.

        """
        transferred, indentation = transplanted
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        resource = project.get_resource(
            target[0].relative_to(Path(project.root.real_path)).as_posix()
        )
        destination = runtime.build_string_module(
            project, updated[target[0]], resource=resource
        )
        owner = destination.get_attribute(target[1]).get_object().get_scope()
        if owner is None:
            message = "payload destination owner has no native source scope"
            raise TypeError(message)
        target_lines = cls._source_lines(updated[target[0]])
        first = target_lines.get_line_start(owner.get_body_start())
        last = min(
            target_lines.get_line_end(owner.get_end()) + 1, len(updated[target[0]])
        )
        body = updated[target[0]][first:last]
        whitespace = body[: len(body) - len(body.lstrip())]
        if not whitespace or "\n" in whitespace:
            whitespace = " " * (
                len(target_lines.get_line(owner.get_start()))
                - len(target_lines.get_line(owner.get_start()).lstrip())
                + len(indentation)
            )
        inserted = indent(transferred.rstrip() + "\n", whitespace)
        if body.strip() == "pass":
            updated[target[0]] = (
                updated[target[0]][:first] + inserted + updated[target[0]][last:]
            )
        else:
            # Local preset references bind only after the target's original body.
            updated[target[0]] = (
                updated[target[0]][:last] + "\n" + inserted + updated[target[0]][last:]
            )
        organized = runtime.module_imports_for_pymodule(
            project,
            runtime.build_string_module(project, updated[target[0]], resource=resource),
        )
        for information in imports:
            organized.add_import(information)
        updated[target[0]] = organized.get_changed_source()

    @classmethod
    def _payload_imports(
        cls,
        project: p.Infra.RopeProject,
        origin: Path,
        target: Path,
        node: p.Infra.RopeScope,
    ) -> t.Pair[
        t.VariadicTuple[p.Infra.RopeImportInfo],
        t.MappingKV[t.Pair[int, int], str],
    ]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        root = Path(project.root.real_path)
        source = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
            project.get_resource(origin.relative_to(root).as_posix()),
            origin,
        ).read()
        destination = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            project.get_resource(target.relative_to(root).as_posix()),
        ).get_scope()
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                project.get_resource(origin.relative_to(root).as_posix()), origin
            ),
        )
        scope = module.get_scope()
        imports: t.MutableMappingKV[str, p.Infra.RopeImportInfo] = {}
        for information in cls.native_import_infos(project, module):
            for name, alias in information.names_and_aliases:
                imports[alias or name.split(".")[0]] = information
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
                isinstance(statement, p.Infra.RopeFromImport) and statement.level
            ):
                msg = (
                    "declaration-relocation: unresolved/outer dependency "
                    f"{origin}:{node.pyobject.get_name()} -> {name}"
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
                aliases = tuple(
                    (imported_name, alias)
                    for imported_name, alias in statement.names_and_aliases
                    if (alias or imported_name.split(".")[0]) == name
                )
                imported = (
                    runtime.from_import(statement.module_name, statement.level, aliases)
                    if isinstance(statement, p.Infra.RopeFromImport)
                    else runtime.normal_import(aliases)
                )
                required.append(imported)
        return tuple(required), dependencies

    @classmethod
    def native_import_infos(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
    ) -> t.VariadicTuple[p.Infra.RopeImportInfo]:
        """Read native import records, including native guarded source regions.

        Returns:
            Every native import record of the module, top-level and guarded.

        Raises:
            ValueError: If native import records differ from their lexical occurrences;
                or if native import token has no enclosing logical statement.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        records = FlextInfraUtilitiesRopeImports.source_import_statements(
            project,
            module.source_code,
        )
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.lexical_occurrence_finder(
            project, "import"
        )
        tokens = tuple(
            occurrence.offset for occurrence in finder.find_occurrences(pymodule=module)
        )
        if len(tokens) != len(records):
            msg = "native import records differ from their lexical occurrences"
            raise ValueError(msg)
        guard = project.get_module("typing").get_attribute("TYPE_CHECKING")
        facts = FlextInfraUtilitiesRopeStructure.logical_statements(module.source_code)
        selected: list[p.Infra.RopeImportInfo] = []
        conditions: list[t.Pair[int, bool]] = []
        position = 0
        for statement in facts:
            while conditions and statement.indent <= conditions[-1][0]:
                conditions.pop()
            words = statement.text.strip().split(maxsplit=1)
            head = words[0].rstrip(":") if words else ""
            if head in {
                "else",
                "elif",
                "except",
                "finally",
                "try",
                "with",
                "for",
                "while",
            }:
                # Module scope does not make a conditional import unconditional.
                # Only the explicitly proven typing guard may be promoted.
                conditions.append((statement.indent, False))
            if statement.category == c.Infra.StatementCategory.IF_GUARD:
                expression = (
                    statement.text.strip().removeprefix("if ").partition(":")[0]
                )
                expression = expression.removesuffix(" is True").strip()
                conditions.append((
                    statement.indent,
                    runtime.same_name(
                        guard,
                        runtime.expression_name(module.get_scope(), expression),
                    ),
                ))
            while position < len(tokens) and tokens[position] < statement.end_offset:
                offset = tokens[position]
                record = records[position]
                position += 1
                if offset < statement.start_offset:
                    msg = "native import token has no enclosing logical statement"
                    raise ValueError(msg)
                if runtime.scope_at(module, offset).get_kind() == "Module" and all(
                    condition for _indent, condition in conditions
                ):
                    selected.append(record.import_info)
        return tuple(selected)

    @staticmethod
    def _dependency_source(
        source: str,
        dependencies: t.MappingKV[t.Pair[int, int], str],
    ) -> str:
        """Rewrite only bound executable attributes, retaining ordinary strings.

        Returns:
            Source rebound to the resolved dependency owners.

        """
        rewrites = sorted(
            (start, stop - start, text) for (start, stop), text in dependencies.items()
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
        node: p.Infra.RopeScope,
        source: str,
        dependencies: t.MappingKV[t.Pair[int, int], str],
    ) -> set[str]:
        """Keep original imports only when transferred code still loads them.

        Returns:
            The unreplaced original dependency roots.

        """
        lines = cls._source_lines(source)
        begin = lines.get_line_start(node.get_start())
        end = min(lines.get_line_end(node.get_end()) + 1, len(source))
        types = FlextInfraUtilitiesSemanticFamilyTypeReferences
        changed = cls._dependency_source(source[begin:end], dependencies)
        remaining = {
            changed[start:stop].split(".")[0]
            for start, stop in types.reference_regions(changed)
        }
        original = cls._payload_loaded_names(project, module, node, source)
        replaced = {
            source[begin + first : begin + last].split(".", maxsplit=1)[0]
            for first, last in dependencies
            if source[begin + first : begin + last]
            .split(".", maxsplit=1)[0]
            .isidentifier()
        }
        for (first, last), text in dependencies.items():
            old = types.string_constant(source[begin + first : begin + last])
            new = types.string_constant(text)
            if old is not None and new is not None:
                replaced.update(
                    cls._quoted_dependency_names(project, module.get_scope(), old)
                    - cls._quoted_dependency_names(project, module.get_scope(), new),
                )
                remaining.update(
                    cls._quoted_dependency_names(project, module.get_scope(), new),
                )
        return original - (replaced - remaining)

    @classmethod
    def _payload_dependency_routes(
        cls,
        context: t.Pair[p.Infra.RopeProject, p.Infra.RopeScope],
        destination: p.Infra.RopeScope,
        target: Path,
        node: p.Infra.RopeScope,
    ) -> t.Pair[
        t.MappingKV[t.Pair[int, int], str],
        list[p.Infra.RopeImportInfo],
    ]:
        """Resolve nested dependencies to their authored declaration identities.

        Conflicting owners surface as ``ValueError`` during owner resolution.

        Returns:
            Attribute replacements and required direct owner imports.

        Raises:
            TypeError: The dependency scope lacks its native source module.

        """
        dependencies: t.MutableMappingKV[t.Pair[int, int], str] = {}
        imports: t.MutableMappingKV[str, p.Infra.RopeImportInfo] = {}
        module = context[1].pyobject.get_module()
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module):
            message = "payload dependency scope has no native source module"
            raise TypeError(message)
        source = module.source_code
        lines = cls._source_lines(source)
        first = lines.get_line_start(node.get_start())
        last = min(lines.get_line_end(node.get_end()) + 1, len(source))
        types = FlextInfraUtilitiesSemanticFamilyTypeReferences
        annotations = types.annotation_regions(source, module)
        for (
            begin,
            end,
        ) in FlextInfraUtilitiesSemanticFamilyTypeReferences.reference_regions(
            source[first:last]
        ):
            item = source[first + begin : first + end]
            if "." not in item:
                continue
            line = next(
                (
                    declaration_line
                    for start, stop, declaration_line in annotations
                    if start <= first + begin < first + end <= stop
                ),
                None,
            )
            lexical = FlextInfraUtilitiesRopeRuntimeModules.scope_at(
                module,
                first + begin,
                declaration_line=line,
            )
            replacement = cls._dependency_replacement(
                (context[0], lexical),
                destination,
                target,
                item,
                imports,
            )
            if replacement is None:
                continue
            dependencies[begin, end] = replacement
        for begin, end, literal, lexical in types.quoted_type_regions(
            source,
            context[0],
            module,
        ):
            if not first <= begin < end <= last:
                continue
            changed = types.rewrite_type_source(
                literal,
                context[0],
                lexical,
                lambda scope, value: cls._dependency_replacement(
                    (context[0], scope),
                    destination,
                    target,
                    value,
                    imports,
                ),
            )
            if changed != literal:
                dependencies[begin - first, end - first] = repr(changed)
        return dependencies, list(imports.values())

    @classmethod
    def _dependency_replacement(
        cls,
        context: t.Pair[p.Infra.RopeProject, p.Infra.RopeScope],
        destination: p.Infra.RopeScope,
        target: Path,
        expression: str,
        imports: t.MutableMappingKV[str, p.Infra.RopeImportInfo],
    ) -> str | None:
        owner = cls._payload_dependency_owner(context, expression, target)
        if owner is None:
            return None
        provider, outer, child = owner
        resource = provider.get_resource()
        if resource is not None and Path(resource.real_path).resolve() == target:
            return child
        existing = destination.get_names().get(outer)
        declared = provider.get_attribute(outer)
        if existing is not None and not FlextInfraUtilitiesRopeRuntimeModules.same_name(
            existing,
            declared,
        ):
            msg = f"declaration-relocation: conflicting dependency {target}:{outer}"
            raise ValueError(msg)
        if existing is None:
            imports[outer] = FlextInfraUtilitiesRopeRuntimeModules.from_import(
                provider.get_name(),
                0,
                ((outer, None),),
            )
        return f"{outer}.{child}"

    @classmethod
    def _payload_dependency_owner(
        cls,
        context: t.Pair[p.Infra.RopeProject, p.Infra.RopeScope],
        item: str,
        target: Path,
    ) -> t.Triple[p.Infra.RopePyModule, str, str] | None:
        """Find a unique same-package nested declaration, never a facade alias.

        Returns:
            The declaring module, outer class and nested declaration, if unique.

        Raises:
            TypeError: The nested declaration has no native source module.

        """
        project, scope = context
        segments = item.split(".")
        imported = FlextInfraUtilitiesRopeRuntimeModules.expression_name(
            scope,
            segments[0],
        )
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
            if binding is not None and len(segments) == _COMPOSED_REFERENCE_SEGMENTS:
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
            binding = FlextInfraUtilitiesRopeRuntimeModules.expression_name(scope, item)
        if binding is None:
            return None
        provider, line = binding.get_definition_location()
        if provider is None or line is None:
            return None
        provider = provider.get_module()
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(provider):
            message = "nested declaration requires a native source module"
            raise TypeError(message)
        resource = provider.get_resource()
        if (
            resource is None
            or Path(resource.real_path).resolve().parent.parent != target.parent.parent
        ):
            return None
        owners = [
            (outer, child)
            for outer in provider.get_scope().get_scopes()
            if outer.get_kind() == "Class"
            for child in outer.get_scopes()
            if child.get_kind() == "Class" and child.get_start() == line
        ]
        return (
            (
                provider,
                owners[0][0].pyobject.get_name(),
                owners[0][1].pyobject.get_name(),
            )
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
            TypeError: An authored declaring owner has no native source module.
            ValueError: If multiple authored owners declare the dependency.

        """
        owners: list[t.Triple[p.Infra.RopePyModule, str, str]] = []
        for ancestor in cls.class_ancestry(composed):
            scope = ancestor.get_scope()
            provider = ancestor.get_module()
            resource = provider.get_resource() if provider is not None else None
            if scope is None or provider is None or resource is None:
                continue
            if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(provider):
                message = "declaration owner requires a native source module"
                raise TypeError(message)
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
        node: p.Infra.RopeScope,
        source: str,
    ) -> set[str]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        first, last = node.get_region()
        resource = module.get_resource()
        loaded: set[str] = set()
        for name, binding in module.get_scope().get_names().items():
            finder = FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
                project,
                name,
                binding,
                imports=False,
                in_hierarchy=False,
            )
            if any(
                not occurrence.is_defined() and first <= occurrence.offset < last
                for occurrence in finder.find_occurrences(resource=resource)
            ):
                loaded.add(name)
        types = FlextInfraUtilitiesSemanticFamilyTypeReferences
        for begin, end, literal, lexical in types.quoted_type_regions(
            source, project, module
        ):
            if first <= begin < end <= last:
                for name in cls._quoted_dependency_names(project, lexical, literal):
                    binding = runtime.expression_name(lexical, name)
                    supplier, line = (
                        binding.get_definition_location()
                        if binding is not None
                        else (None, None)
                    )
                    if (
                        supplier is module
                        and line is not None
                        and (node.get_start() <= line <= node.get_end())
                    ):
                        continue
                    loaded.add(name)
        return loaded

    @classmethod
    def _quoted_dependency_names(
        cls,
        project: p.Infra.RopeProject,
        scope: p.Infra.RopeScope,
        source: str,
    ) -> set[str]:
        names: set[str] = set()

        def collect(_scope: p.Infra.RopeScope, expression: str) -> None:
            names.add(expression.partition(".")[0])

        FlextInfraUtilitiesSemanticFamilyTypeReferences.rewrite_type_source(
            source,
            project,
            scope,
            collect,
        )
        return names

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
