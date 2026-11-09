"""Derive authored Protocol surfaces and upstream facade owners natively.

The model-to-protocol projector compares a projected contract with an authored
Protocol and names upstream structural bases. Both facts are read from Rope's
native class graph; no list of packages or members is kept here.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections import deque
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import closing
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
        """Read the native declaring module and full lexical class path.

        Returns:
            The resulting ``str``.

        """
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
        """Enumerate actual nested Protocol declarations, excluding composing owners.

        Returns:
            The resulting ``tuple[p.Infra.RopeSourceClass, ...]``.

        """
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
        """Reuse the projector's authenticated model-to-protocol origin inventory.

        Returns:
            The resulting ``Mapping[str, str]``.

        """
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
        """Bind narrowing contracts to the foreign classes their predicates admit.

        Returns:
            The resulting ``Mapping[str, tuple[str, ...]]``.

        """
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
                if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                narrowed = cls._guard_contract(project, module, node, guards)
                if narrowed is None:
                    continue
                contract, body_scope = narrowed
                for call, scope in cls._native_guard_calls(node, body_scope, sources):
                    for operand in cls._isinstance_operands(project, call, scope):
                        native = cls._narrowing_operand(project, operand, scope)
                        if native is not None and (
                            (resource := native.get_module().get_resource()) is None
                            or Path(resource.real_path).resolve() not in sources
                        ):
                            origins.setdefault(
                                cls._contract_identity(contract, project=project), []
                            ).append(
                                f"{path}:{node.lineno}: native narrowing to "
                                f"{cls._contract_identity(native, project=project)}"
                            )
        return {
            identity: tuple(dict.fromkeys(evidence))
            for identity, evidence in origins.items()
        }

    @staticmethod
    def _guard_contract(
        project: p.Infra.RopeProject,
        module: p.Infra.RopeSourceModule,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        guards: Sequence[p.Infra.RopePyName],
    ) -> tuple[p.Infra.RopeSourceClass, p.Infra.RopeScope] | None:
        runtime = FlextInfraUtilitiesRopeRuntime
        if not isinstance(node.returns, ast.Subscript):
            return None
        scope = runtime.scope_at(
            module,
            module.get_source_binding_index().lines[node][0],
            declaration_line=node.lineno,
        )
        guard = runtime.annotation_origin(project, node.returns.value, scope)
        if guard is None or not any(
            runtime.same_name(guard, value) for value in guards
        ):
            return None
        target = runtime.annotation_origin(project, node.returns.slice, scope)
        if target is None or not runtime.py_class(contract := target.get_object()):
            return None
        return contract, module.get_scope().get_inner_scope_for_line(
            node.body[0].lineno
        )

    @staticmethod
    def _isinstance_operands(
        project: p.Infra.RopeProject, call: ast.Call, scope: p.Infra.RopeScope
    ) -> Sequence[ast.expr]:
        runtime = FlextInfraUtilitiesRopeRuntime
        expected = runtime.qualified_name(project, "isinstance", module_name="builtins")
        if not runtime.same_name(
            expected, runtime.expression_name(scope, ast.unparse(call.func))
        ):
            return ()
        match call.args:
            case [_, ast.Tuple(elts=operands)]:
                return operands
            case [_, operand]:
                return (operand,)
            case _:
                return ()

    @classmethod
    def _narrowing_operand(
        cls, project: p.Infra.RopeProject, operand: ast.expr, scope: p.Infra.RopeScope
    ) -> p.Infra.RopeSourceClass | None:
        runtime = FlextInfraUtilitiesRopeRuntime
        supplier = runtime.annotation_origin(project, operand, scope)
        match operand:
            case ast.Call(args=[provider_node, name_node]):
                expected = runtime.qualified_name(
                    project,
                    "FlextInfraUtilitiesRopeRuntimeBase.runtime_type",
                    module_name="flext_infra._utilities._rope.runtime_base",
                )
                if runtime.same_name(
                    expected, runtime.expression_name(scope, ast.unparse(operand.func))
                ):
                    provider = cls._native_guard_string(provider_node, scope)
                    name = cls._native_guard_string(name_node, scope)
                    if provider is not None and name is not None:
                        supplier = runtime.qualified_name(
                            project, name, module_name=provider
                        )
        if supplier is not None and runtime.py_class(native := supplier.get_object()):
            return native
        return None

    @staticmethod
    def _native_guard_calls(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        scope: p.Infra.RopeScope,
        sources: Mapping[Path, str],
    ) -> Iterator[tuple[ast.Call, p.Infra.RopeScope]]:
        """Follow source-defined predicate wrappers through native callable bindings.

        Yields:
            Each ``tuple[ast.Call, p.Infra.RopeScope]``.

        """
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
        node: ast.expr,
        scope: p.Infra.RopeScope,
    ) -> str | None:
        """Read a literal or its native constant declaration without executing code.

        Returns:
            The resulting ``str | None``.

        """
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
        """Inventory native origins, complete public routes and dependencies.

        Returns:
            The resulting ``p.Infra.ProtocolPlacementCensus``.

        """
        origins = cls._external_protocol_origins(workspace.rope_project, sources)
        model_origins = cls._native_protocol_models(workspace)
        references = {
            f"{item.module_name}.{item.scope_path}": tuple(
                site
                for site in item.all_reference_sites
                if Path(site.file_path).resolve() in sources
            )
            for item in objects
        }
        observed = tuple(
            cls._protocol_row(
                workspace,
                contract,
                cls._protocol_origin(
                    workspace, contract, origins, model_origins, references
                ),
            )
            for contract in cls._declared_protocols(workspace, sources)
        )
        return cls._protocol_dependencies(
            workspace.repository_root, observed, references
        )

    @classmethod
    def _declared_protocols(
        cls, workspace: p.Infra.RopeWorkspaceDsl, sources: Mapping[Path, str]
    ) -> Iterator[p.Infra.RopeSourceClass]:
        runtime = FlextInfraUtilitiesRopeRuntime
        protocol = runtime.qualified_name(
            workspace.rope_project, "Protocol", module_name="typing"
        ).get_object()
        for path in sorted(sources):
            if "_protocols" in path.parts and path.is_relative_to(
                workspace.repository_root
            ):
                yield from cls._protocol_classes(
                    runtime.require_source_module(
                        workspace.rope_project.get_pymodule(
                            runtime.file_resource_at(workspace.rope_project, path)
                        )
                    ),
                    protocol,
                )

    @classmethod
    def _protocol_origin(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        contract: p.Infra.RopeSourceClass,
        origins: Mapping[str, tuple[str, ...]],
        model_origins: Mapping[str, str],
        references: Mapping[str, Sequence[p.Infra.ReferenceSite]],
    ) -> tuple[c.Infra.ProtocolOrigin, tuple[str, ...]]:
        identity = cls._contract_identity(contract, project=workspace.rope_project)
        if identity in model_origins:
            return c.Infra.ProtocolOrigin.MODEL, (
                f"native model declaration: {model_origins[identity]}",
            )
        if evidence := origins.get(identity, ()):
            return c.Infra.ProtocolOrigin.EXTERNAL, evidence
        resource = contract.get_module().get_resource()
        if resource is None:
            message = f"native protocol has no source resource: {identity}"
            raise ValueError(message)
        family = next(
            parent
            for parent in Path(resource.real_path).parents
            if parent.name == "_protocols"
        )
        for site in references.get(identity, ()):
            consumer = Path(site.file_path).resolve()
            if (
                not consumer.is_relative_to(family)
                and site.offset is not None
                and (
                    cls._native_di_port_use(
                        workspace.rope_project, consumer, site.offset
                    )
                )
            ):
                return c.Infra.ProtocolOrigin.SERVICE, (
                    f"native DI capability consumed at {consumer}:{site.line}",
                )
        return c.Infra.ProtocolOrigin.UNRESOLVED, ()

    @classmethod
    def _protocol_public_routes(
        cls, project: p.Infra.RopeProject, contract: p.Infra.RopeSourceClass
    ) -> tuple[str, ...]:
        runtime = FlextInfraUtilitiesRopeRuntime
        resource = contract.get_module().get_resource()
        if resource is None:
            message = "native protocol has no source resource"
            raise ValueError(message)
        family = next(
            parent
            for parent in Path(resource.real_path).parents
            if parent.name == "_protocols"
        )
        module = runtime.require_source_module(
            project.get_pymodule(
                runtime.file_resource_at(project, family.parent / "protocols.py")
            )
        )
        binding = module.get_attributes().get("p")
        if binding is None or not runtime.py_class(facade := binding.get_object()):
            return ()
        pending = deque([
            (facade, "p", frozenset({cls._contract_identity(facade, project=project)}))
        ])
        public: list[str] = []
        while pending:
            owner, prefix, ancestry = pending.popleft()
            for name, member in owner.get_attributes().items():
                value = member.get_object()
                if value is contract:
                    public.append(f"{prefix}.{name}")
                elif runtime.py_class(value):
                    identity = cls._contract_identity(value, project=project)
                    if identity not in ancestry:
                        pending.append((
                            value,
                            f"{prefix}.{name}",
                            ancestry | {identity},
                        ))
        return tuple(dict.fromkeys(public))

    @classmethod
    def _protocol_destination(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        contract: p.Infra.RopeSourceClass,
        category: c.Infra.ProtocolOrigin,
    ) -> tuple[str, str, Path]:
        project = workspace.rope_project
        resource = contract.get_module().get_resource()
        if resource is None:
            message = "native protocol has no source resource"
            raise ValueError(message)
        path = Path(resource.real_path).resolve()
        family = next(parent for parent in path.parents if parent.name == "_protocols")
        module = FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
            contract.get_module(), source_project=project
        )
        name = cls._contract_identity(contract, project=project).removeprefix(
            module + "."
        )
        if category not in {
            c.Infra.ProtocolOrigin.SERVICE,
            c.Infra.ProtocolOrigin.EXTERNAL,
        } or path.relative_to(family).parts[0] in {"_services", "_external"}:
            return module, name, path.relative_to(workspace.repository_root)
        grouping, suffix = (
            ("_services", "Services")
            if category is c.Infra.ProtocolOrigin.SERVICE
            else ("_external", "External")
        )
        facade = (
            FlextInfraUtilitiesRopeRuntime
            .require_source_module(
                project.get_pymodule(
                    FlextInfraUtilitiesRopeRuntime.file_resource_at(
                        project, family.parent / "protocols.py"
                    )
                )
            )
            .get_attributes()
            .get("p")
        )
        holder = name.partition(".")[0]
        stem = (
            facade.get_object().get_name()
            if (
                facade is not None
                and FlextInfraUtilitiesRopeRuntime.py_class(facade.get_object())
            )
            else holder
        )
        destination = family / grouping / path.relative_to(family)
        return (
            ".".join((
                module.split("._protocols", 1)[0],
                "_protocols",
                *destination.relative_to(family).with_suffix("").parts,
            )),
            stem + suffix + holder.removeprefix(stem) + "." + name.partition(".")[2],
            destination.relative_to(workspace.repository_root),
        )

    @classmethod
    def _protocol_row(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        contract: p.Infra.RopeSourceClass,
        origin: tuple[c.Infra.ProtocolOrigin, tuple[str, ...]],
    ) -> tuple[p.Infra.ProtocolContractPlacement, int]:
        project = workspace.rope_project
        resource = contract.get_module().get_resource()
        if resource is None:
            message = "native protocol has no source resource"
            raise ValueError(message)
        module = FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
            contract.get_module(), source_project=project
        )
        native = contract.get_ast()
        if not isinstance(native, ast.ClassDef):
            message = "protocol has no native class declaration"
            raise TypeError(message)
        destination = cls._protocol_destination(workspace, contract, origin[0])
        return (
            m.Infra.ProtocolContractPlacement(
                source_module=module,
                source_class=cls._contract_identity(
                    contract, project=project
                ).removeprefix(module + "."),
                source_path=Path(resource.real_path)
                .resolve()
                .relative_to(workspace.repository_root),
                line=native.lineno,
                category=origin[0],
                destination_module=destination[0],
                destination_class=destination[1],
                destination_path=destination[2],
                public_routes=cls._protocol_public_routes(project, contract),
                evidence=origin[1],
            ),
            native.end_lineno or contract.get_scope().get_end(),
        )

    @staticmethod
    def _protocol_dependencies(
        root: Path,
        observed: Sequence[tuple[p.Infra.ProtocolContractPlacement, int]],
        references: Mapping[str, Sequence[p.Infra.ReferenceSite]],
    ) -> p.Infra.ProtocolPlacementCensus:
        bounds = {
            row.source_module + "." + row.source_class: (
                root / row.source_path,
                row.line,
                last,
            )
            for row, last in observed
        }
        dependencies: dict[str, set[str]] = {identity: set() for identity in bounds}
        declarations: dict[Path, list[tuple[str, int, int]]] = {}
        for identity, (path, first, last) in bounds.items():
            declarations.setdefault(path, []).append((identity, first, last))
        for target in bounds:
            for site in references.get(target, ()):
                for identity, first, last in declarations.get(
                    Path(site.file_path).resolve(), ()
                ):
                    if identity != target and first <= site.line <= last:
                        dependencies[identity].add(target)
        return m.Infra.ProtocolPlacementCensus.model_validate({
            "contracts": tuple(
                row.model_copy(
                    update={
                        "dependencies": tuple(
                            sorted(
                                dependencies[row.source_module + "." + row.source_class]
                            )
                        )
                    }
                )
                for row, _last in observed
            ),
            "findings": tuple(
                f"{identity}: no native model, supplier or first-party capability "
                f"consumer"
                for row, _last in observed
                if row.category is c.Infra.ProtocolOrigin.UNRESOLVED
                for identity in (row.source_module + "." + row.source_class,)
            ),
        })

    @staticmethod
    def _native_di_port_use(
        project: p.Infra.RopeProject, path: Path, offset: int
    ) -> bool:
        """Prove that the occurrence is an operand of the canonical DI Port alias.

        Returns:
            The resulting ``bool``.

        """
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

    @classmethod
    def _protocol_composition_source(
        cls,
        project: p.Infra.RopeProject,
        namespace: p.Infra.RopeSourceClass,
        dependency: tuple[str, str],
    ) -> tuple[Path, str]:
        """Compose a native holder through indexed class-header and import ports.

        Returns:
            The resulting ``tuple[Path, str]``.

        Raises:
            ValueError: If protocol facade has no source resource.
            TypeError: If protocol namespace lost its native class identity.

        """
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
        imported_root, _separator, tail = name.partition(".")
        source, imported = u.type_adapter(tuple[str, str]).validate_python(
            runtime.runtime_callable("rope.refactor.importutils", "add_import")(
                project, module, provider, imported_root
            ),
            strict=True,
        )
        expression = imported + ("." + tail if tail else "")
        identity = cls._contract_identity(namespace, project=project)
        declaring_module = FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
            module, source_project=project
        )
        refreshed = runtime.build_string_module(project, source, resource=resource)
        current = refreshed
        for part in identity.removeprefix(declaring_module + ".").split("."):
            current = current.get_attribute(part).get_object()
        if not runtime.py_class(current):
            msg_0 = f"protocol namespace lost its native class identity: {identity}"
            raise TypeError(msg_0)
        layout = refreshed.get_source_binding_index().class_layout(current.get_scope())
        if layout.arguments_region is None:
            start = stop = layout.bases_insertion_offset
            text = f"({expression})"
        else:
            start, _end = layout.arguments_region
            stop = start
            text = f"{expression}, "
        changed = runtime.content_change(
            resource,
            source,
            (m.Infra.SourceRewrite(start=start, end=stop, text=text),),
        ).new_contents
        return path, changed

    @classmethod
    def _protocol_namespace_source(
        cls,
        project: p.Infra.RopeProject,
        owner: p.Infra.RopeSourceClass,
        name: str,
    ) -> str:
        """Materialize a namespace through the shared template and native sourceutils.

        Returns:
            The resulting ``str``.

        Raises:
            TypeError: If protocol namespace has no local declaring scope.
            ValueError: If protocol namespace owner has no source; or if protocol
                namespace destination is occupied.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        module = runtime.require_source_module(owner.get_module())
        resource = module.get_resource()
        if resource is None:
            msg = "protocol namespace owner has no source"
            raise ValueError(msg)
        source = module.source_code
        inherited = owner.get_attributes().get(name)
        bases: tuple[str, ...] = ()
        if inherited is not None:
            value = inherited.get_object()
            if not runtime.py_class(value):
                msg = f"protocol namespace destination is occupied: {name}"
                raise ValueError(msg)
            if value.get_module().get_resource() == resource:
                return source
            provider = FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                value.get_module(), source_project=project
            )
            identity = cls._contract_identity(value, project=project).removeprefix(
                provider + "."
            )
            root, _separator, tail = identity.partition(".")
            source, imported = u.type_adapter(tuple[str, str]).validate_python(
                runtime.runtime_callable("rope.refactor.importutils", "add_import")(
                    project, module, provider, root
                ),
                strict=True,
            )
            bases = (imported + ("." + tail if tail else ""),)
        snippet = FlextInfraUtilitiesFacadeComponents.generate_module_skeleton(
            context=m.Infra.ModuleSkeletonRenderContext(
                class_name=name,
                base_class=None,
                base_module=None,
                docstring="Compose structural capability namespaces.",
                module_prefix="",
                class_bases=bases,
            )
        ).unwrap()
        current = runtime.build_string_module(project, source, resource=resource)
        declaring_module = FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
            module, source_project=project
        )
        path = cls._contract_identity(owner, project=project).removeprefix(
            declaring_module + "."
        )
        bound = runtime.expression_name(current.get_scope(), path)
        if bound is None or not runtime.py_class(namespace := bound.get_object()):
            msg = f"protocol namespace has no local declaring scope: {path}"
            raise TypeError(msg)
        return u.type_adapter(str).validate_python(
            runtime.runtime_callable("rope.refactor.sourceutils", "add_methods")(
                current, namespace.get_scope(), (snippet,)
            ),
            strict=True,
        )

    @classmethod
    def _protocol_parent_scaffolds(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
        targets: Sequence[tuple[Path, str, str]],
    ) -> Mapping[Path, str]:
        """Create every native destination parent scope, without a depth budget.

        Returns:
            The resulting ``Mapping[Path, str]``.

        Raises:
            TypeError: If protocol destination parent is not a source class.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        working = dict(sources)
        for path, module_name, parent in targets:
            parents = parent.split(".")
            for index, name in enumerate(parents[1:], start=1):
                project = runtime.snapshot_project(workspace.rope_project, working)
                try:
                    owner = runtime.qualified_name(
                        project, ".".join(parents[:index]), module_name=module_name
                    ).get_object()
                    if not runtime.py_class(owner):
                        msg = (
                            f"protocol destination parent is not a source class: "
                            f"{parents[:index]}"
                        )
                        raise TypeError(msg)
                    working[path] = cls._protocol_namespace_source(project, owner, name)
                finally:
                    project.close()
        return working

    @classmethod
    def _protocol_destination_sources(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
        placements: Sequence[p.Infra.ProtocolContractPlacement],
    ) -> Mapping[Path, str]:
        """Prepare empty destination holders and composition-only category owners.

        Returns:
            The resulting ``Mapping[Path, str]``.

        """
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
                            "Compose structural capability owners without another "
                            "public namespace.\n\n"
                            + FlextInfraUtilitiesLintRecipes.copyright_notice(
                                family.parent, module=aggregate, source_project=project
                            )
                        ),
                    )
                ).unwrap()
            )
        return cls._protocol_parent_scaffolds(
            workspace,
            working,
            tuple(
                (
                    root / row.destination_path,
                    row.destination_module,
                    row.destination_class.rpartition(".")[0],
                )
                for row in placements
            ),
        )

    @classmethod
    def _protocol_binding_sources(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
        placements: Sequence[p.Infra.ProtocolContractPlacement],
    ) -> Mapping[Path, str]:
        """Compose each public namespace with its own destination parent scope.

        Returns:
            The resulting ``Mapping[Path, str]``.

        Raises:
            TypeError: If category namespace has no native class; or if public namespace
                has no native class.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        root = workspace.repository_root
        working = dict(sources)
        for row in placements:
            target = root / row.destination_path
            family = next(
                parent for parent in target.parents if parent.name == "_protocols"
            )
            category = target.relative_to(family).parts[0].lstrip("_")
            provider = (
                row.source_module.partition("._protocols")[0]
                + f"._protocols.{category}"
            )
            aggregate_path = family / f"{category}.py"
            project = runtime.snapshot_project(workspace.rope_project, working)
            try:
                module = runtime.require_source_module(project.get_module(provider))
                aggregate_owner = next(
                    scope.pyobject.get_name()
                    for scope in module.get_scope().get_scopes()
                    if scope.get_kind() == "Class"
                )
            finally:
                project.close()
            for route in row.public_routes or (None,):
                public_parents = () if route is None else tuple(route.split(".")[1:-1])
                aggregate_parent = ".".join((aggregate_owner, *public_parents))
                working = dict(
                    cls._protocol_parent_scaffolds(
                        workspace,
                        working,
                        ((aggregate_path, provider, aggregate_parent),),
                    )
                )
                project = runtime.snapshot_project(workspace.rope_project, working)
                try:
                    aggregate = runtime.qualified_name(
                        project, aggregate_parent, module_name=provider
                    ).get_object()
                    if not runtime.py_class(aggregate):
                        msg = (
                            f"category namespace has no native class: "
                            f"{aggregate_parent}"
                        )
                        raise TypeError(msg)
                    path, content = cls._protocol_composition_source(
                        project,
                        aggregate,
                        (
                            row.destination_module,
                            row.destination_class.rpartition(".")[0],
                        ),
                    )
                    working[path] = content
                finally:
                    project.close()
                if route is None:
                    continue
                project = runtime.snapshot_project(workspace.rope_project, working)
                try:
                    facade = (
                        row.source_module.partition("._protocols")[0] + ".protocols"
                    )
                    receiver = runtime.qualified_name(
                        project, route.rpartition(".")[0], module_name=facade
                    ).get_object()
                    if not runtime.py_class(receiver):
                        msg = f"public namespace has no native class: {route}"
                        raise TypeError(msg)
                    path, content = cls._protocol_composition_source(
                        project,
                        receiver,
                        (
                            row.destination_module,
                            row.destination_class.rpartition(".")[0],
                        ),
                    )
                    working[path] = content
                finally:
                    project.close()
        return working

    @classmethod
    def plan_protocol_contract_organization(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: Mapping[Path, str],
        census: p.Infra.ProtocolPlacementCensus,
    ) -> p.Infra.ProtocolOrganizationPlan:
        """Place and rewire censused protocols before the caller projects them.

        Returns:
            The resulting ``p.Infra.ProtocolOrganizationPlan``.

        Raises:
            TypeError: If protocol placement has no native class identity; or if public
                protocol receiver is not a source class; or if native protocol class
                transfer returned a non-content effect.
            ValueError: If native protocol rewire escaped its source inventory.

        """
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
        working = dict(cls._protocol_binding_sources(workspace, working, placements))
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
                    row.destination_class.rpartition(".")[0],
                    module_name=row.destination_module,
                ).get_object()
                if not runtime.py_class(origin) or not runtime.py_class(destination):
                    msg = (
                        f"protocol placement has no native class identity: "
                        f"{row.source_module}.{row.source_class}"
                    )
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
                        msg = (
                            "native protocol class transfer returned a non-content "
                            "effect"
                        )
                        raise TypeError(msg)
                    path = Path(change.resource.real_path).resolve()
                    if path not in working:
                        msg = (
                            f"native protocol rewire escaped its source inventory: "
                            f"{path}"
                        )
                        raise ValueError(msg)
                    working[path] = (
                        FlextInfraUtilitiesSemanticDeclarationRelocation.remove_orphaned_imports(
                            project, change.resource, working[path], change.new_contents
                        )
                    )
            finally:
                project.close()
        working.update(
            cls._protocol_self_imports(
                base,
                working,
                tuple({root / row.destination_path for row in placements}),
            )
        )
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

    @staticmethod
    def _protocol_self_imports(
        base: p.Infra.RopeProject,
        sources: Mapping[Path, str],
        paths: Sequence[Path],
    ) -> Mapping[Path, str]:
        """Let native import tools spell moved recursive contracts locally.

        Returns:
            Self-import rewrites preserving every other import and source use.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        with closing(runtime.snapshot_project(base, sources)) as project:
            tools = runtime.import_organizer(project).import_tools
            return {
                path: tools.organize_imports(
                    runtime.require_source_module(
                        project.get_pymodule(runtime.file_resource_at(project, path))
                    ),
                    unused=False,
                    duplicates=False,
                    sort=False,
                )
                for path in paths
            }

    @classmethod
    def _validate_protocol_public_bindings(
        cls,
        base: p.Infra.RopeProject,
        sources: Mapping[Path, str],
        inventory: Sequence[p.Infra.ProtocolContractPlacement],
        placements: Sequence[p.Infra.ProtocolContractPlacement],
    ) -> None:
        """Prove every published contract still names its elected declaration.

        Raises:
            ValueError: If protocol placement changed public binding.

        """
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
                        msg = (
                            f"protocol placement changed public binding "
                            f"{facade}:{route}; expected {expected}"
                        )
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
