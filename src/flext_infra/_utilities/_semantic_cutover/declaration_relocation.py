"""Immutable, identity-bound payload relocation and settings/config import rewires.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent, indent

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCodemodProject,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeStructure,
)
from flext_infra._utilities._rope_source_bases_aliases import (
    FlextInfraUtilitiesRopeSourceBasesAliases,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)
from flext_infra._utilities._semantic_cutover.declaration_relocation_imports import (
    FlextInfraUtilitiesSemanticDeclarationRelocationImports,
)


class FlextInfraUtilitiesSemanticDeclarationRelocation(
    FlextInfraUtilitiesSemanticDeclarationRelocationImports,
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
        # One closed epoch serves every snapshot of this pass: the sources, their
        # import closure and the identities payload relocation resolves.
        epoch = FlextInfraUtilitiesCodemodProject.identity_source_epoch(
            Path(workspace.rope_project.root.real_path),
            tuple(sources),
            c.Infra.DECLARATION_RELOCATION_IDENTITIES,
        )
        project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            workspace.rope_project, sources, captured=epoch
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
                    workspace.rope_project, working, captured=epoch
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
                    candidate = cls._next_payload(project, path, unresolved)
                    if candidate is None:
                        break
                    outer_name = candidate[0].pyobject.get_name()
                    node_name = candidate[1].pyobject.get_name()
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
                        (path, candidate[1], candidate[2]),
                        resolved,
                    )
                    # Subsequent candidates bind to the proposed graph and coordinates.
                    project.close()
                    project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                        workspace.rope_project, working, captured=epoch
                    )
            cls.preflight_semantic_import_graph(workspace, sources, working)
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
            FlextInfraUtilitiesRopeCore
            .resolve_pymodule(
                project,
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
    def _next_payload(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
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
            module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                project,
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
            FlextInfraUtilitiesRopeCore
            .resolve_pymodule(
                project,
                project.get_resource(declaration[0].relative_to(root).as_posix()),
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
                FlextInfraUtilitiesRopeCore
                .resolve_pymodule(
                    project,
                    project.get_resource(path.relative_to(root).as_posix()),
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
        facade = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            project.get_resource(
                (package / c.Infra.MODELS_PY).relative_to(root).as_posix(),
            ),
        )
        initializer = package / c.Infra.INIT_PY
        resource = project.get_resource(initializer.relative_to(root).as_posix())
        initializer_module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project, resource
        )
        exports = FlextInfraUtilitiesRopeSourceBasesAliases.lazy_module_aliases(
            initializer_module.get_name(),
            initializer,
            FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                resource,
                initializer,
            ).read(),
            project=project,
            pymodule=initializer_module,
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
            FlextInfraUtilitiesRopeCore
            .resolve_pymodule(
                project,
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
        expected = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
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

    @staticmethod
    def preflight_semantic_import_graph(
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
