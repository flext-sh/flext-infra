"""Derive authored Protocol surfaces and upstream facade owners natively.

The model-to-protocol projector compares a projected contract with an authored
Protocol and names upstream structural bases. Both facts are read from Rope's
native class graph; no list of packages or members is kept here.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path

from flext_cli import u

from flext_infra import c, m, p, t
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeRuntime,
)
from flext_infra._utilities._semantic_cutover.declaration_relocation import (
    FlextInfraUtilitiesSemanticDeclarationRelocation,
)
from flext_infra._utilities.facade_components import FlextInfraUtilitiesFacadeComponents
from flext_infra._utilities.lint_recipes import FlextInfraUtilitiesLintRecipes
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery
from flext_infra._utilities.workspace_snapshot import (
    FlextInfraUtilitiesWorkspaceSnapshot,
)


class FlextInfraUtilitiesModelsProtocolContracts:
    """Read structural Protocol members and upstream facades from native ancestry."""

    @staticmethod
    def _contract_identity(
        value: p.Infra.RopeSourceClass, *, project: p.Infra.RopeProject
    ) -> str:
        """Read the native declaring module and full lexical class path."""
        names: list[str] = []
        scope = value.get_scope()
        while scope.get_kind() == "Class":
            names.append(scope.pyobject.get_name())
            if scope.parent is None:
                break
            scope = scope.parent
        module = FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
            value.get_module(), source_project=project
        )
        return f"{module}.{'.'.join(reversed(names))}"

    @classmethod
    def _protocol_classes(
        cls, module: p.Infra.RopeSourceModule, protocol: p.Infra.RopePyObject
    ) -> tuple[p.Infra.RopeSourceClass, ...]:
        """Enumerate actual nested Protocol declarations, excluding composing owners."""
        runtime = FlextInfraUtilitiesRopeRuntime
        found: list[p.Infra.RopeSourceClass] = []
        pending = list(module.get_scope().get_scopes())
        while pending:
            scope = pending.pop()
            if scope.get_kind() != "Class":
                continue
            value = scope.pyobject
            if not runtime.py_class(value):
                continue
            pending.extend(scope.get_scopes())
            if (
                scope.parent is not None
                and scope.parent.get_kind() == "Class"
                and protocol in value.get_mro()
            ):
                found.append(value)
        return tuple(found)

    @classmethod
    def _native_protocol_models(
        cls, workspace: p.Infra.RopeWorkspaceDsl
    ) -> Mapping[str, str]:
        """Reuse the projector's authenticated model-to-protocol origin inventory."""
        return {
            protocol: model
            for model, protocol in workspace.model_protocol_identities.items()
        }

    @classmethod
    def _external_protocol_origins(
        cls,
        project: p.Infra.RopeProject,
        sources: Mapping[Path, str],
    ) -> Mapping[str, tuple[str, ...]]:
        """Bind narrowing contracts to the foreign classes their predicates admit."""
        runtime = FlextInfraUtilitiesRopeRuntime
        guards = tuple(
            runtime.qualified_name(project, name, module_name="typing")
            for name in ("TypeGuard", "TypeIs")
        )
        origins: dict[str, list[str]] = {}
        for path in sources:
            module = runtime.require_source_module(
                project.get_pymodule(runtime.file_resource_at(project, path))
            )
            for node in ast.walk(module.get_ast()):
                if not isinstance(
                    node, ast.FunctionDef | ast.AsyncFunctionDef
                ) or not isinstance(node.returns, ast.Subscript):
                    continue
                scope = runtime.scope_at(
                    module,
                    module.get_source_binding_index().lines[node][0],
                    declaration_line=node.lineno,
                )
                guard = runtime.annotation_origin(project, node.returns.value, scope)
                if guard is None or not any(
                    runtime.same_name(guard, expected) for expected in guards
                ):
                    continue
                target = runtime.annotation_origin(project, node.returns.slice, scope)
                if target is None or not runtime.py_class(
                    contract := target.get_object()
                ):
                    continue
                body_scope = module.get_scope().get_inner_scope_for_line(
                    node.body[0].lineno
                )
                for call, call_scope in cls._native_guard_calls(
                    node, body_scope, sources
                ):
                    if not isinstance(call, ast.Call) or len(call.args) != 2:
                        continue
                    predicate = runtime.expression_name(
                        call_scope, ast.unparse(call.func)
                    )
                    if predicate is None or not runtime.same_name(
                        predicate,
                        runtime.qualified_name(
                            project, "isinstance", module_name="builtins"
                        ),
                    ):
                        continue
                    operands = (
                        call.args[1].elts
                        if isinstance(call.args[1], ast.Tuple)
                        else (call.args[1],)
                    )
                    for operand in operands:
                        supplier = runtime.annotation_origin(
                            project, operand, call_scope
                        )
                        if isinstance(operand, ast.Call) and len(operand.args) == 2:
                            loader = runtime.expression_name(
                                call_scope, ast.unparse(operand.func)
                            )
                            declared = runtime.qualified_name(
                                project,
                                "FlextInfraUtilitiesRopeRuntimeBase.runtime_type",
                                module_name="flext_infra._utilities._rope.runtime_base",
                            )
                            if loader is not None and runtime.same_name(
                                loader, declared
                            ):
                                provider = cls._native_guard_string(
                                    project, operand.args[0], call_scope
                                )
                                name = cls._native_guard_string(
                                    project, operand.args[1], call_scope
                                )
                                if provider is not None and name is not None:
                                    supplier = runtime.qualified_name(
                                        project, name, module_name=provider
                                    )
                        if supplier is None or not runtime.py_class(
                            native := supplier.get_object()
                        ):
                            continue
                        resource = native.get_module().get_resource()
                        if (
                            resource is not None
                            and Path(resource.real_path).resolve() in sources
                        ):
                            continue
                        origins.setdefault(
                            cls._contract_identity(contract, project=project), []
                        ).append(
                            f"{path}:{node.lineno}: native narrowing to {cls._contract_identity(native, project=project)}"
                        )
        return {
            identity: tuple(dict.fromkeys(evidence))
            for identity, evidence in origins.items()
        }

    @staticmethod
    def _native_guard_calls(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        scope: p.Infra.RopeScope,
        sources: Mapping[Path, str],
    ) -> Iterator[tuple[ast.Call, p.Infra.RopeScope]]:
        """Follow source-defined predicate wrappers through native callable bindings."""
        runtime = FlextInfraUtilitiesRopeRuntime
        pending = [(node, scope)]
        seen: set[int] = set()
        while pending:
            declaration, lexical = pending.pop()
            if id(declaration) in seen:
                continue
            seen.add(id(declaration))
            for call in ast.walk(declaration):
                if not isinstance(call, ast.Call):
                    continue
                yield call, lexical
                binding = runtime.expression_name(lexical, ast.unparse(call.func))
                if binding is None or not runtime.py_function(
                    function := binding.get_object()
                ):
                    continue
                resource = function.get_module().get_resource()
                if (
                    resource is not None
                    and Path(resource.real_path).resolve() in sources
                ):
                    pending.append((function.get_ast(), function.get_scope()))

    @staticmethod
    def _native_guard_string(
        project: p.Infra.RopeProject,
        node: ast.expr,
        scope: p.Infra.RopeScope,
    ) -> str | None:
        """Read a literal or its native constant declaration without executing code."""
        runtime = FlextInfraUtilitiesRopeRuntime
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        binding = runtime.expression_name(scope, ast.unparse(node))
        if binding is None:
            return None
        provider, line = runtime.definition_location(binding)
        if line is None or not runtime.source_module(provider):
            return None
        lexical = provider.get_scope().get_inner_scope_for_line(line)
        values: set[str] = set()
        for assignment in provider.get_source_binding_index().assignment_layouts(
            lexical, name=ast.unparse(node).rsplit(".", 1)[-1]
        ):
            if assignment.value is None:
                return None
            first, last = assignment.value
            value = runtime.literal_string(provider.source_code[first:last])
            if value is None:
                return None
            values.add(value)
        return next(iter(values)) if len(values) == 1 else None

    @classmethod
    def protocol_contract_census(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: Mapping[Path, str],
        objects: Sequence[p.Infra.Object] = (),
    ) -> p.Infra.ProtocolPlacementCensus:
        """Inventory all origins and canonical placements before any source effect."""
        project = workspace.rope_project
        root = workspace.repository_root
        protocol_sources = tuple(
            path
            for path in sorted(sources)
            if "_protocols" in path.parts and path.is_relative_to(root)
        )
        if not protocol_sources:
            return m.Infra.ProtocolPlacementCensus()
        runtime = FlextInfraUtilitiesRopeRuntime
        protocol = runtime.qualified_name(
            project, "Protocol", module_name="typing"
        ).get_object()
        origins = cls._external_protocol_origins(project, sources)
        model_origins = cls._native_protocol_models(workspace)
        reference_sites = {
            f"{item.module_name}.{item.scope_path}": item.all_reference_sites
            for item in objects
        }
        rows: list[p.Infra.ProtocolContractPlacement] = []
        findings: list[str] = []
        bounds: dict[str, tuple[Path, int, int]] = {}
        for path in protocol_sources:
            family = next(
                parent for parent in path.parents if parent.name == "_protocols"
            )
            module = runtime.require_source_module(
                project.get_pymodule(runtime.file_resource_at(project, path))
            )
            module_name = FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                module, source_project=project
            )
            facade_path = family.parent / "protocols.py"
            facade_module = runtime.require_source_module(
                project.get_pymodule(runtime.file_resource_at(project, facade_path))
            )
            facade_binding = facade_module.get_attributes().get("p")
            facade = None if facade_binding is None else facade_binding.get_object()
            for contract in cls._protocol_classes(module, protocol):
                identity = cls._contract_identity(contract, project=project)
                scope = contract.get_scope()
                native = contract.get_ast()
                if not isinstance(native, ast.ClassDef):
                    msg = f"protocol has no native class declaration: {identity}"
                    raise TypeError(msg)
                bounds[identity] = (
                    path,
                    native.lineno,
                    native.end_lineno or scope.get_end(),
                )
                relative = path.relative_to(family)
                evidence = origins.get(identity, ())
                category = (
                    c.Infra.ProtocolOrigin.EXTERNAL
                    if evidence
                    else c.Infra.ProtocolOrigin.UNRESOLVED
                )
                if identity in model_origins:
                    category, evidence = (
                        c.Infra.ProtocolOrigin.MODEL,
                        (f"native model declaration: {model_origins[identity]}",),
                    )
                if category is c.Infra.ProtocolOrigin.UNRESOLVED:
                    for occurrence in reference_sites.get(identity, ()):
                        consumer = Path(occurrence.file_path).resolve()
                        if (
                            consumer in sources
                            and not consumer.is_relative_to(family)
                            and occurrence.offset is not None
                            and cls._native_di_port_use(
                                project, consumer, occurrence.offset
                            )
                        ):
                            category = c.Infra.ProtocolOrigin.SERVICE
                            evidence = (
                                f"native DI capability consumed at {consumer}:{occurrence.line}",
                            )
                            break
                public: list[str] = []
                namespaces = [(facade, "p")] if facade is not None else []
                for owner, prefix in namespaces:
                    for name, binding in owner.get_attributes().items():
                        value = binding.get_object()
                        if value is contract:
                            public.append(f"{prefix}.{name}")
                        elif (
                            runtime.py_class(value)
                            and value.get_module() is facade_module
                            and len(prefix.split(".")) < 3
                        ):
                            namespaces.append((value, f"{prefix}.{name}"))
                current_class = identity.removeprefix(module_name + ".")
                destination, destination_class = path, current_class
                if category in {
                    c.Infra.ProtocolOrigin.SERVICE,
                    c.Infra.ProtocolOrigin.EXTERNAL,
                } and relative.parts[0] not in {"_services", "_external"}:
                    grouping = (
                        "_services"
                        if category is c.Infra.ProtocolOrigin.SERVICE
                        else "_external"
                    )
                    destination = family / grouping / relative
                    holder = current_class.partition(".")[0]
                    suffix = (
                        "Services"
                        if category is c.Infra.ProtocolOrigin.SERVICE
                        else "External"
                    )
                    facade_name = (
                        facade.get_name() if runtime.py_class(facade) else holder
                    )
                    destination_holder = (
                        facade_name + suffix + holder.removeprefix(facade_name)
                    )
                    destination_class = (
                        destination_holder + "." + current_class.partition(".")[2]
                    )
                destination_module = ".".join((
                    module_name.split("._protocols", 1)[0],
                    "_protocols",
                    *destination.relative_to(family).with_suffix("").parts,
                ))
                if category is c.Infra.ProtocolOrigin.UNRESOLVED:
                    findings.append(
                        f"{identity}: no native model, supplier or first-party capability consumer"
                    )
                rows.append(
                    m.Infra.ProtocolContractPlacement(
                        source_module=module_name,
                        source_class=current_class,
                        source_path=path.relative_to(root),
                        line=native.lineno,
                        category=category,
                        destination_module=destination_module,
                        destination_class=destination_class,
                        destination_path=destination.relative_to(root),
                        public_routes=tuple(public),
                        evidence=evidence,
                    )
                )
        dependencies: dict[str, set[str]] = {identity: set() for identity in bounds}
        declarations_by_file: dict[Path, list[tuple[str, int, int]]] = {}
        for identity, (path, first, last) in bounds.items():
            declarations_by_file.setdefault(path, []).append((identity, first, last))
        for target, sites in reference_sites.items():
            if target not in bounds:
                continue
            for site in sites:
                for identity, first, last in declarations_by_file.get(
                    Path(site.file_path).resolve(), ()
                ):
                    if identity != target and first <= site.line <= last:
                        dependencies[identity].add(target)
        return m.Infra.ProtocolPlacementCensus(
            contracts=tuple(
                row.model_copy(
                    update={
                        "dependencies": tuple(
                            sorted(
                                dependencies[row.source_module + "." + row.source_class]
                            )
                        )
                    }
                )
                for row in rows
            ),
            findings=tuple(findings),
        )

    @staticmethod
    def _native_di_port_use(
        project: p.Infra.RopeProject, path: Path, offset: int
    ) -> bool:
        """Prove that the occurrence is an operand of the canonical DI Port alias."""
        runtime = FlextInfraUtilitiesRopeRuntime
        module = runtime.require_source_module(
            project.get_pymodule(runtime.file_resource_at(project, path))
        )
        port = runtime.qualified_name(
            project, "t.Port", module_name="flext_core.typings"
        )
        index = module.get_source_binding_index()
        for node in ast.walk(module.get_ast()):
            if not isinstance(node, ast.Subscript):
                continue
            first, last = index.lines[node.slice]
            if first is None or last is None or not first <= offset < last:
                continue
            scope = runtime.scope_at(module, first, declaration_line=node.lineno)
            binding = runtime.expression_name(scope, ast.unparse(node.value))
            if binding is not None and runtime.same_name(binding, port):
                return True
        return False

    @staticmethod
    def protocol_contract_reference_filter(
        project: p.Infra.RopeProject,
        source_module: str,
        public_routes: Sequence[str],
    ) -> Callable[[p.Infra.RopeOccurrence], bool]:
        """Retain proven public facade receivers during native identity rewiring.

        The same filter is consumed by producer movement and portable replay.
        It never recognizes a receiver from the spelling of its local alias.

        Returns:
            The native occurrence predicate, true only for references to rewrite.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        module = source_module.partition("._protocols")[0] + ".protocols"
        preserved = tuple(
            runtime.qualified_name(
                project, route.rpartition(".")[0], module_name=module
            ).get_object()
            for route in public_routes
        )

        def selected(occurrence: p.Infra.RopeOccurrence) -> bool:
            names = occurrence.get_primary_and_pyname()
            if names is None or names[0] is None:
                return True
            receiver = names[0].get_object()
            return all(receiver is not facade for facade in preserved)

        return selected

    @staticmethod
    def _protocol_composition_source(
        project: p.Infra.RopeProject,
        namespace: p.Infra.RopeSourceClass,
        dependency: tuple[str, str],
    ) -> tuple[Path, str]:
        """Compose a native holder through indexed class-header and import ports."""
        runtime = FlextInfraUtilitiesRopeRuntime
        provider, name = dependency
        module = runtime.require_source_module(namespace.get_module())
        resource = module.get_resource()
        if resource is None:
            msg = "protocol facade has no source resource"
            raise ValueError(msg)
        path = Path(resource.real_path).resolve()
        source = module.source_code
        layout = module.get_source_binding_index().class_layout(namespace.get_scope())
        expected = runtime.qualified_name(project, name, module_name=provider)
        if any(
            binding is not None and runtime.same_name(binding, expected)
            for _region, binding in layout.base_bindings
        ):
            return path, source
        if layout.arguments_region is None:
            start = stop = layout.bases_insertion_offset
            text = f"({name})"
        else:
            start, _end = layout.arguments_region
            stop = start
            text = f"{name}, "
        changed = runtime.content_change(
            resource,
            source,
            (m.Infra.SourceRewrite(start=start, end=stop, text=text),),
        ).new_contents
        imports = runtime.module_imports_for_pymodule(
            project, runtime.build_string_module(project, changed, resource=resource)
        )
        imports.add_import(runtime.from_import(provider, 0, ((name, None),)))
        return path, imports.get_changed_source()

    @classmethod
    def _protocol_destination_sources(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
        placements: Sequence[p.Infra.ProtocolContractPlacement],
    ) -> Mapping[Path, str]:
        """Prepare empty destination holders and composition-only category owners."""
        root = workspace.repository_root
        project = workspace.rope_project
        working = dict(sources)
        groups: set[Path] = set()
        for row in placements:
            target = root / row.destination_path
            holder = row.destination_class.partition(".")[0]
            family = next(
                parent for parent in target.parents if parent.name == "_protocols"
            )
            if target not in working:
                working[target] = (
                    FlextInfraUtilitiesFacadeComponents.generate_module_skeleton(
                        context=m.Infra.ModuleSkeletonRenderContext(
                            class_name=holder,
                            base_class=None,
                            base_module=None,
                            docstring=(
                                f"Own {row.category.value} capability contracts.\n\n"
                                + FlextInfraUtilitiesLintRecipes.copyright_notice(
                                    family.parent, module=target, source_project=project
                                )
                            ),
                        )
                    ).unwrap()
                )
            category = target.relative_to(family).parts[0]
            for directory in target.parents:
                if directory == family:
                    break
                initializer = directory / c.Infra.INIT_PY
                if initializer not in working:
                    working[initializer] = '"""Structural capability contracts."""\n'
            aggregate = family / f"{category.lstrip('_')}.py"
            groups.add(aggregate)
        for aggregate in sorted(groups):
            if aggregate in working:
                continue
            family = aggregate.parent
            facade = (
                FlextInfraUtilitiesRopeRuntime
                .require_source_module(
                    project.get_pymodule(
                        FlextInfraUtilitiesRopeRuntime.file_resource_at(
                            project, family.parent / "protocols.py"
                        )
                    )
                )
                .get_attribute("p")
                .get_object()
            )
            owner = facade.get_name() + u.derive_class_stem(aggregate.stem)
            working[aggregate] = (
                FlextInfraUtilitiesFacadeComponents.generate_module_skeleton(
                    context=m.Infra.ModuleSkeletonRenderContext(
                        class_name=owner,
                        base_class=None,
                        base_module=None,
                        docstring=(
                            "Compose structural capability owners without another public namespace.\n\n"
                            + FlextInfraUtilitiesLintRecipes.copyright_notice(
                                family.parent, module=aggregate, source_project=project
                            )
                        ),
                    )
                ).unwrap()
            )
        return working

    @classmethod
    def plan_protocol_contract_organization(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: Mapping[Path, str],
        census: p.Infra.ProtocolPlacementCensus,
    ) -> p.Infra.ProtocolOrganizationPlan:
        """Census first, native placement/rewiring next; projection is the caller's phase."""
        runtime = FlextInfraUtilitiesRopeRuntime
        root, base = workspace.repository_root, workspace.rope_project
        placements = tuple(
            row
            for row in census.contracts
            if row.category
            in {c.Infra.ProtocolOrigin.SERVICE, c.Infra.ProtocolOrigin.EXTERNAL}
            and row.source_path != row.destination_path
            and not any(
                other.source_module == row.source_module
                and row.source_class.startswith(other.source_class + ".")
                and other.source_path != other.destination_path
                for other in census.contracts
            )
        )
        indexed = {
            row.source_module + "." + row.source_class: row for row in placements
        }
        graph = {
            identity: set(row.dependencies) & indexed.keys()
            for identity, row in indexed.items()
        }
        cohorts = {
            min(members): members for members in u.Cli.dag_strongly_connected(graph)
        }
        owners = {
            identity: owner
            for owner, members in cohorts.items()
            for identity in members
        }
        condensed = {
            owner: {
                owners[dependency]
                for identity in members
                for dependency in graph[identity]
                if owners[dependency] != owner
            }
            for owner, members in cohorts.items()
        }
        placements = tuple(
            indexed[identity]
            for owner in u.Cli.dag_order(condensed).unwrap()
            for identity in sorted(cohorts[owner])
        )
        working = dict(
            cls._protocol_destination_sources(workspace, sources, placements)
        )
        for row in placements:
            project = runtime.snapshot_project(base, working)
            try:
                target = root / row.destination_path
                family = next(
                    parent for parent in target.parents if parent.name == "_protocols"
                )
                category = target.relative_to(family).parts[0].lstrip("_")
                provider = (
                    row.source_module.partition("._protocols")[0]
                    + f"._protocols.{category}"
                )
                aggregate = runtime.require_source_module(project.get_module(provider))
                owner = next(
                    scope.pyobject
                    for scope in aggregate.get_scope().get_scopes()
                    if scope.get_kind() == "Class"
                )
                aggregate_path, aggregate_source = cls._protocol_composition_source(
                    project,
                    owner,
                    (row.destination_module, row.destination_class.partition(".")[0]),
                )
                working[aggregate_path] = aggregate_source
                for route in row.public_routes:
                    receiver = runtime.qualified_name(
                        project,
                        route.rpartition(".")[0],
                        module_name=row.source_module.partition("._protocols")[0]
                        + ".protocols",
                    ).get_object()
                    if not runtime.py_class(receiver):
                        msg = f"public protocol receiver is not a source class: {route}"
                        raise TypeError(msg)
                    path, content = cls._protocol_composition_source(
                        project, receiver, (provider, owner.get_name())
                    )
                    working[path] = content
            finally:
                project.close()
        before_move = dict(working)
        for row in placements:
            project = runtime.snapshot_project(base, working)
            try:
                source, target = root / row.source_path, root / row.destination_path
                origin = runtime.qualified_name(
                    project, row.source_class, module_name=row.source_module
                ).get_object()
                destination = runtime.qualified_name(
                    project,
                    row.destination_class.partition(".")[0],
                    module_name=row.destination_module,
                ).get_object()
                if not runtime.py_class(origin) or not runtime.py_class(destination):
                    msg = f"protocol placement has no native class identity: {row.source_module}.{row.source_class}"
                    raise TypeError(msg)
                origin_module = runtime.require_source_module(origin.get_module())
                destination_module = runtime.require_source_module(
                    destination.get_module()
                )
                changes = runtime.move_class_changes(
                    project,
                    runtime.file_resource_at(project, source),
                    origin_module
                    .get_source_binding_index()
                    .class_layout(origin.get_scope())
                    .name_region[0],
                    runtime.file_resource_at(project, target),
                    resources=tuple(
                        runtime.file_resource_at(project, path) for path in working
                    ),
                    destination_offset=destination_module
                    .get_source_binding_index()
                    .class_layout(destination.get_scope())
                    .name_region[0],
                    match_filter=cls.protocol_contract_reference_filter(
                        project, row.source_module, row.public_routes
                    ),
                )
                for change in changes.changes:
                    if not isinstance(change, p.Infra.RopeChangeContents):
                        msg = "native protocol class transfer returned a non-content effect"
                        raise TypeError(msg)
                    path = Path(change.resource.real_path).resolve()
                    if path not in working:
                        msg = f"native protocol rewire escaped its source inventory: {path}"
                        raise ValueError(msg)
                    working[path] = (
                        FlextInfraUtilitiesSemanticDeclarationRelocation.remove_orphaned_imports(
                            project, change.resource, working[path], change.new_contents
                        )
                    )
            finally:
                project.close()
        plans = FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
            root,
            (),
            {
                path: source
                for path, source in working.items()
                if sources.get(path) != source
            },
            source_project=base,
        )
        cls._validate_protocol_public_bindings(
            base, working, census.contracts, placements
        )
        return m.Infra.ProtocolOrganizationPlan(
            census=m.Infra.ProtocolPlacementCensus(contracts=placements),
            files=plans,
            pre_move_sources=before_move,
            findings=census.findings,
        )

    @classmethod
    def _validate_protocol_public_bindings(
        cls,
        base: p.Infra.RopeProject,
        sources: Mapping[Path, str],
        inventory: Sequence[p.Infra.ProtocolContractPlacement],
        placements: Sequence[p.Infra.ProtocolContractPlacement],
    ) -> None:
        """Prove every published contract still names its elected declaration."""
        runtime = FlextInfraUtilitiesRopeRuntime
        moves = sorted(
            (
                (
                    row.source_module + "." + row.source_class,
                    row.destination_module + "." + row.destination_class,
                )
                for row in placements
            ),
            key=lambda pair: len(pair[0]),
            reverse=True,
        )
        project = runtime.snapshot_project(base, sources)
        try:
            for row in inventory:
                expected = row.source_module + "." + row.source_class
                for origin, target in moves:
                    if expected == origin or expected.startswith(origin + "."):
                        expected = target + expected.removeprefix(origin)
                        break
                facade = row.source_module.partition("._protocols")[0] + ".protocols"
                for route in row.public_routes:
                    value = runtime.qualified_name(
                        project, route, module_name=facade
                    ).get_object()
                    if (
                        not runtime.py_class(value)
                        or cls._contract_identity(value, project=project) != expected
                    ):
                        msg = f"protocol placement changed public binding {facade}:{route}; expected {expected}"
                        raise ValueError(msg)
        finally:
            project.close()

    @staticmethod
    def protocol_contract_members(
        project: p.Infra.RopeProject,
        protocol: p.Infra.RopeSourceClass,
        protocols_root: Path,
    ) -> dict[str, tuple[t.Infra.AstStatement, Path]]:
        """Collect every member an authored Protocol declares.

        Members inherited from the project's own Protocol ancestors count with
        the declared ones, in native MRO precedence, so a composed contract
        is read as its complete structural surface: attributes, properties
        and callables alike.

        Returns:
            Each member's declaring statement and declaring source path.

        Raises:
            TypeError: A declaring Protocol has no authenticated source AST.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        protocol_base = runtime.qualified_name(
            project, "Protocol", module_name="typing"
        ).get_object()
        root = protocols_root.resolve()
        members: dict[str, tuple[t.Infra.AstStatement, Path]] = {}
        for ancestor in reversed(protocol.get_mro()):
            if (
                not runtime.py_class(ancestor)
                or ancestor is protocol_base
                or protocol_base not in ancestor.get_mro()
            ):
                continue
            resource = ancestor.get_module().get_resource()
            if resource is None:
                continue
            path = Path(resource.real_path).resolve()
            if not path.is_relative_to(root):
                continue
            declaration = ancestor.get_ast()
            if not isinstance(declaration, ast.ClassDef):
                message = "authored contract has no authenticated class AST"
                raise TypeError(message)
            for statement in declaration.body:
                if isinstance(statement, ast.AnnAssign) and isinstance(
                    statement.target, ast.Name
                ):
                    members[statement.target.id] = (statement, path)
                elif isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef):
                    members[statement.name] = (statement, path)
        return members

    @staticmethod
    def upstream_protocol_facade(
        chain: Sequence[p.Infra.RopePyObject],
        package: Path,
        port: p.Infra.RopeSourceClass,
        *,
        source_project: p.Infra.RopeProject,
    ) -> tuple[str, str]:
        """Elect the nearest upstream published ``p`` facade that exposes ``port``.

        A Protocol base is evaluated while its class is created, so it is named
        through an upstream facade the package composes, never through the
        package's own facade under assembly. ``chain`` is the own facade's
        native ancestry closed by the port's declaring facade.

        Returns:
            The upstream facade class name and its package import statement.

        Raises:
            ValueError: No upstream published facade exposes ``port``.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        analysis = FlextInfraUtilitiesRopeAnalysis
        for ancestor in chain:
            if not runtime.py_class(ancestor):
                continue
            module = ancestor.get_module()
            resource = module.get_resource()
            if resource is None or Path(resource.real_path).is_relative_to(package):
                continue
            published = module.get_attributes().get("p")
            exposed = ancestor.get_attributes().get(port.get_name())
            if (
                published is None
                or published.get_object() is not ancestor
                or "p" not in analysis.public_export_names_source(module)
                or exposed is None
                or exposed.get_object() is not port
            ):
                continue
            # The declared source identity, not Rope's source-folder-relative
            # name: a repository namespace package keeps its namespace prefix.
            provider = analysis.package_name_for_module(
                FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                    module, source_project=source_project
                ),
                resource,
            )
            name = ancestor.get_name()
            return name, f"from {provider} import {name}"
        message = f"protocol facade chain has no upstream owner of {port.get_name()}"
        raise ValueError(message)


__all__: list[str] = ["FlextInfraUtilitiesModelsProtocolContracts"]
