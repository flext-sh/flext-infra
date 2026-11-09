"""Derive authored Protocol surfaces and upstream facade owners natively.

The model-to-protocol projector compares a projected contract with an authored
Protocol and names upstream structural bases. Both facts are read from Rope's
native class graph; no list of packages or members is kept here.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_infra import c, m, p, r, t
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeRuntime,
)
from flext_infra._utilities._rope.runtime_modules import FlextInfraUtilitiesRopeRuntimeModules
from flext_infra._utilities._rope.runtime_refactors import FlextInfraUtilitiesRopeRuntimeRefactors
from flext_infra._utilities._rope.runtime_types import FlextInfraUtilitiesRopeRuntimeTypes
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery


class FlextInfraUtilitiesModelsProtocolContracts:
    """Read structural Protocol members and upstream facades from native ancestry."""

    @staticmethod
    def _contract_identity(value: p.Infra.RopeSourceClass) -> str:
        """Read the native declaring module and full lexical class path."""
        names: list[str] = []
        scope = value.get_scope()
        while scope.get_kind() == "Class":
            names.append(scope.pyobject.get_name())
            if scope.parent is None:
                break
            scope = scope.parent
        return f"{value.get_module().get_name()}.{'.'.join(reversed(names))}"

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

    @staticmethod
    def _native_protocol_model(
        project: p.Infra.RopeProject,
        source: Path,
        root: Path,
        contract: p.Infra.RopeSourceClass,
    ) -> bool:
        """Prove the corresponding declaration against the concrete model source."""
        runtime = FlextInfraUtilitiesRopeRuntime
        models = root.parent / "_models" / source.relative_to(root)
        if not project.source_query(models, "isfile"):
            return False
        module = runtime.require_source_module(
            project.get_pymodule(runtime.file_resource_at(project, models))
        )
        parent = contract.get_scope().parent
        names = [contract.get_name()]
        while parent is not None and parent.parent is not None and parent.parent.get_kind() == "Class":
            names.append(parent.pyobject.get_name())
            parent = parent.parent
        base = runtime.qualified_name(project, "BaseModel", module_name="pydantic").get_object()
        for scope in module.get_scope().get_scopes():
            if scope.get_kind() != "Class":
                continue
            value = scope.pyobject
            for name in reversed(names):
                binding = value.get_attributes().get(name)
                if binding is None:
                    break
                value = binding.get_object()
            else:
                if runtime.py_class(value) and base in value.get_mro():
                    return True
        return False

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
                if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) or not isinstance(node.returns, ast.Subscript):
                    continue
                scope = runtime.scope_at(module, module.get_source_binding_index().lines[node][0], declaration_line=node.lineno)
                guard = runtime.annotation_origin(project, node.returns.value, scope)
                if guard is None or not any(runtime.same_name(guard, expected) for expected in guards):
                    continue
                target = runtime.annotation_origin(project, node.returns.slice, scope)
                if target is None or not runtime.py_class(contract := target.get_object()):
                    continue
                for call in ast.walk(node):
                    if not isinstance(call, ast.Call) or len(call.args) != 2:
                        continue
                    predicate = runtime.expression_name(scope, ast.unparse(call.func))
                    if predicate is None or not runtime.same_name(predicate, runtime.qualified_name(project, "isinstance", module_name="builtins")):
                        continue
                    operands = call.args[1].elts if isinstance(call.args[1], ast.Tuple) else (call.args[1],)
                    for operand in operands:
                        supplier = runtime.annotation_origin(project, operand, scope)
                        if isinstance(operand, ast.Call) and len(operand.args) == 2:
                            loader = runtime.expression_name(scope, ast.unparse(operand.func))
                            declared = runtime.qualified_name(project, "FlextInfraUtilitiesRopeRuntimeBase.runtime_type", module_name="flext_infra._utilities._rope.runtime_base")
                            if loader is not None and runtime.same_name(loader, declared) and all(isinstance(arg, ast.Constant) and isinstance(arg.value, str) for arg in operand.args):
                                supplier = runtime.qualified_name(project, operand.args[1].value, module_name=operand.args[0].value)
                        if supplier is None or not runtime.py_class(native := supplier.get_object()):
                            continue
                        resource = native.get_module().get_resource()
                        if resource is not None and Path(resource.real_path).resolve() in sources:
                            continue
                        origins.setdefault(cls._contract_identity(contract), []).append(
                            f"{path}:{node.lineno}: native narrowing to {cls._contract_identity(native)}"
                        )
        return {identity: tuple(dict.fromkeys(evidence)) for identity, evidence in origins.items()}

    @classmethod
    def protocol_contract_census(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: Mapping[Path, str],
    ) -> p.Infra.ProtocolPlacementCensus:
        """Inventory all origins and canonical placements before any source effect."""
        project = workspace.rope_project
        root = workspace.repository_root
        runtime = FlextInfraUtilitiesRopeRuntime
        protocol = runtime.qualified_name(project, "Protocol", module_name="typing").get_object()
        origins = cls._external_protocol_origins(project, sources)
        rows: list[p.Infra.ProtocolContractPlacement] = []
        findings: list[str] = []
        for path in sorted(sources):
            if "_protocols" not in path.parts or not path.is_relative_to(root):
                continue
            family = next(parent for parent in path.parents if parent.name == "_protocols")
            module = runtime.require_source_module(project.get_pymodule(runtime.file_resource_at(project, path)))
            facade_path = family.parent / "protocols.py"
            facade_module = runtime.require_source_module(project.get_pymodule(runtime.file_resource_at(project, facade_path)))
            facade_binding = facade_module.get_attributes().get("p")
            facade = None if facade_binding is None else facade_binding.get_object()
            for contract in cls._protocol_classes(module, protocol):
                identity = cls._contract_identity(contract)
                scope = contract.get_scope()
                native = contract.get_ast()
                if not isinstance(native, ast.ClassDef):
                    raise TypeError(f"protocol has no native class declaration: {identity}")
                relative = path.relative_to(family)
                evidence = origins.get(identity, ())
                category = "external" if evidence else "unresolved"
                if cls._native_protocol_model(project, path, family, contract):
                    category, evidence = "model", (f"native model declaration: {family.parent / '_models' / relative}",)
                elif relative.parts[0] in {"_services", "_external"}:
                    category = "service" if relative.parts[0] == "_services" else "external"
                    evidence = (*evidence, "authored canonical category placement")
                if category == "unresolved":
                    offset = module.get_source_binding_index().class_layout(scope).name_region[0]
                    for occurrence in runtime.runtime_find_occurrences(project, runtime.file_resource_at(project, path), offset, resources=None, in_hierarchy=False):
                        resource = occurrence.resource
                        if resource is None:
                            continue
                        consumer = Path(resource.real_path).resolve()
                        if consumer in sources and not consumer.is_relative_to(family):
                            category = "service"
                            evidence = (f"first-party capability consumed at {consumer}:{occurrence.lineno}",)
                            break
                public: list[str] = []
                namespaces = [(facade, "p")] if facade is not None else []
                for owner, prefix in namespaces:
                    for name, binding in owner.get_attributes().items():
                        value = binding.get_object()
                        if value is contract:
                            public.append(f"{prefix}.{name}")
                        elif runtime.py_class(value) and value.get_module() is facade_module and len(prefix.split(".")) < 3:
                            namespaces.append((value, f"{prefix}.{name}"))
                current_class = identity.removeprefix(module.get_name() + ".")
                destination, destination_class = path, current_class
                if category in {"service", "external"} and relative.parts[0] not in {"_services", "_external"}:
                    grouping = "_services" if category == "service" else "_external"
                    destination = family / grouping / relative
                    holder = current_class.partition(".")[0]
                    suffix = "Services" if category == "service" else "External"
                    destination_class = holder + suffix + "." + current_class.partition(".")[2]
                destination_module = ".".join((module.get_name().split("._protocols", 1)[0], "_protocols", *destination.relative_to(family).with_suffix("").parts))
                if category == "unresolved":
                    findings.append(f"{identity}: no native model, supplier or first-party capability consumer")
                rows.append(m.Infra.ProtocolContractPlacement(
                    source_module=module.get_name(), source_class=current_class,
                    source_path=path.relative_to(root), line=native.lineno, category=category,
                    destination_module=destination_module, destination_class=destination_class,
                    destination_path=destination.relative_to(root), public_routes=tuple(public), evidence=evidence,
                ))
        return m.Infra.ProtocolPlacementCensus(contracts=tuple(rows), findings=tuple(findings))

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
