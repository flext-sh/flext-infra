"""Preserve mutable opaque ports through their proven protocol element type.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_cli import u

from flext_infra import m, p
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._semantic_cutover.model_envelopes import (
    FlextInfraUtilitiesSemanticModelEnvelopes,
)
from flext_infra._utilities.workspace_snapshot import (
    FlextInfraUtilitiesWorkspaceSnapshot,
)


class FlextInfraUtilitiesSemanticOpaquePorts:
    """Let native identities prove both a mutator and its opaque model field."""

    @staticmethod
    def _identity(scope: p.Infra.RopeScope, node: ast.expr) -> str:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        if not isinstance(node, ast.Name | ast.Attribute):
            return ""
        binding = runtime.expression_name(scope, ast.unparse(node))
        return (
            ""
            if binding is None
            else runtime.native_object_identity(binding.get_object())
        )

    @classmethod
    def _twins(
        cls, project: p.Infra.RopeProject, routes: Mapping[str, str]
    ) -> dict[str, tuple[p.Infra.RopeSourceClass, str]]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        twins: dict[str, tuple[p.Infra.RopeSourceClass, str]] = {}
        for model, protocol in routes.items():
            if model.startswith("m."):
                continue
            concrete = runtime.qualified_name(project, model).get_object()
            if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(concrete):
                continue
            projected = runtime.qualified_name(
                project, f"{model.partition('.')[0]}.{protocol}"
            ).get_object()
            twins[runtime.native_object_identity(projected)] = (concrete, protocol)
        return twins

    @classmethod
    def _proof(
        cls,
        module: p.Infra.RopeSourceModule,
        issue: p.Infra.Issue,
        twins: Mapping[str, tuple[p.Infra.RopeSourceClass, str]],
    ) -> tuple[p.Infra.RopeSourceClass, str, str] | None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        scope = runtime.scope_at(
            module, module.lines.get_line_start(issue.line) + issue.column - 1
        )
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_function(scope.pyobject):
            return None
        function = scope.pyobject.get_ast()
        if not isinstance(function, ast.FunctionDef) or function.returns is None:
            return None
        element = cls._identity(scope, function.returns)
        if element not in twins:
            return None
        writes = (
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and node.lineno == issue.line
            and isinstance(node.targets[0], ast.Subscript)
            and isinstance(node.targets[0].value, ast.Attribute)
            and isinstance(node.targets[0].value.value, ast.Name)
            and isinstance(node.value, ast.Name)
        )
        for write in writes:
            target = write.targets[0]
            if (
                not isinstance(write.value, ast.Name)
                or not isinstance(target, ast.Subscript)
                or not isinstance(target.value, ast.Attribute)
                or not isinstance(target.value.value, ast.Name)
            ):
                continue
            if not cls._returned_value(module, scope, function, write.value):
                continue
            for parameter in (*function.args.posonlyargs, *function.args.args):
                if (
                    parameter.arg != target.value.value.id
                    or parameter.annotation is None
                ):
                    continue
                owner = cls._identity(scope, parameter.annotation)
                if owner in twins:
                    return twins[owner][0], target.value.attr, element
        return None

    @staticmethod
    def _returned_value(
        module: p.Infra.RopeSourceModule,
        scope: p.Infra.RopeScope,
        function: ast.FunctionDef,
        value: ast.Name,
    ) -> bool:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        expected = runtime.expression_name(scope, value.id)
        return expected is not None and any(
            isinstance(returned, ast.Return)
            and isinstance(returned.value, ast.Name)
            and runtime.same_name(
                expected,
                runtime.expression_name(
                    runtime.scope_at(
                        module, runtime.source_offset(module.source_code, returned)
                    ),
                    returned.value.id,
                ),
            )
            for returned in ast.walk(function)
        )

    @classmethod
    def _parameter_owner(
        cls,
        scope: p.Infra.RopeScope,
        function: ast.FunctionDef,
        name: str,
        twins: Mapping[str, tuple[p.Infra.RopeSourceClass, str]],
    ) -> p.Infra.RopeSourceClass | None:
        candidates = {
            cls._identity(scope, node)
            for parameter in (
                *function.args.posonlyargs,
                *function.args.args,
                *function.args.kwonlyargs,
            )
            if parameter.arg == name and parameter.annotation is not None
            for node in ast.walk(parameter.annotation)
            if isinstance(node, ast.expr) and cls._identity(scope, node) in twins
        }
        return twins[next(iter(candidates))][0] if len(candidates) == 1 else None

    @staticmethod
    def _mutables(project: p.Infra.RopeProject) -> frozenset[str]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        return frozenset(
            runtime.native_object_identity(
                runtime.qualified_name(project, name).get_object()
            )
            for name in (
                "builtins.dict",
                "builtins.list",
                "collections.abc.MutableMapping",
                "collections.abc.MutableSequence",
            )
        )

    @classmethod
    def _argument_proof(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopeSourceModule,
        issue: p.Infra.Issue,
        twins: Mapping[str, tuple[p.Infra.RopeSourceClass, str]],
    ) -> tuple[p.Infra.RopeSourceClass, str, str] | None:
        pair = FlextInfraUtilitiesSemanticModelEnvelopes.model_argument_diagnostic(
            issue
        )
        if pair is None:
            return None
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        scope = runtime.scope_at(
            module, module.lines.get_line_start(issue.line) + issue.column - 1
        )
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_function(scope.pyobject):
            return None
        function = scope.pyobject.get_ast()
        if not isinstance(function, ast.FunctionDef):
            return None
        for invocation in ast.walk(function):
            if not isinstance(invocation, ast.Call):
                continue
            for keyword in invocation.keywords:
                if (
                    keyword.arg != pair[1]
                    or keyword.value.end_lineno is None
                    or (
                        not keyword.value.lineno
                        <= issue.line
                        <= keyword.value.end_lineno
                    )
                ):
                    continue
                value = keyword.value
                if (
                    isinstance(value, ast.IfExp)
                    and isinstance(value.orelse, ast.Constant)
                    and value.orelse.value is None
                ):
                    value = value.body
                if not isinstance(value, ast.Attribute) or not isinstance(
                    value.value, ast.Name
                ):
                    continue
                owner = cls._parameter_owner(scope, function, value.value.id, twins)
                element = cls._mutable_parameter_element(
                    project, scope, invocation.func, pair[1], twins
                )
                if owner is not None and element is not None:
                    return owner, value.attr, element
        return None

    @classmethod
    def _mutable_parameter_element(
        cls,
        project: p.Infra.RopeProject,
        scope: p.Infra.RopeScope,
        called: ast.expr,
        parameter: str,
        twins: Mapping[str, tuple[p.Infra.RopeSourceClass, str]],
    ) -> str | None:
        binding = FlextInfraUtilitiesRopeRuntimeModules.expression_name(
            scope, ast.unparse(called)
        )
        if binding is None or not FlextInfraUtilitiesRopeRuntimeTypes.py_function(
            function := binding.get_object()
        ):
            return None
        declaration = function.get_ast()
        if not isinstance(declaration, ast.FunctionDef):
            return None
        elements = {
            cls._identity(function.get_scope(), element)
            for argument in (
                *declaration.args.posonlyargs,
                *declaration.args.args,
                *declaration.args.kwonlyargs,
            )
            if argument.arg == parameter and argument.annotation is not None
            for collection in ast.walk(argument.annotation)
            if isinstance(collection, ast.Subscript)
            and cls._identity(function.get_scope(), collection.value)
            in cls._mutables(project)
            for element in ast.walk(collection.slice)
            if isinstance(element, ast.expr)
            and cls._identity(function.get_scope(), element) in twins
        }
        return next(iter(elements)) if len(elements) == 1 else None

    @classmethod
    def _field_matches(
        cls,
        project: p.Infra.RopeProject,
        proof: tuple[p.Infra.RopeSourceClass, str, str],
        twins: Mapping[str, tuple[p.Infra.RopeSourceClass, str]],
    ) -> tuple[p.Infra.RopeSourceModule, tuple[int, ...]] | None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        owner, field, element = proof
        module = owner.get_module()
        declaration = owner.get_ast()
        if not isinstance(declaration, ast.ClassDef):
            return None
        annotation = next(
            (
                node.annotation
                for node in declaration.body
                if isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == field
            ),
            None,
        )
        if annotation is None:
            return None
        scope = owner.get_scope()
        destination = runtime.expression_name(scope, twins[element][1])
        destination_id = (
            None
            if destination is None
            else runtime.native_object_identity(destination.get_object())
        )
        u.Cli.info(
            f"mod: opaque-port owner={runtime.native_object_identity(owner)} "
            f"field={field} goal={twins[element][1]} "
            f"destination={destination_id} "
            f"expected={element}"
        )
        if (
            destination is None
            or runtime.native_object_identity(destination.get_object()) != element
        ):
            return None
        port = runtime.qualified_name(project, "flext_core.t.Port")
        mutable = cls._mutables(project)
        concrete = runtime.native_object_identity(twins[element][0])
        offsets = []
        for opaque in ast.walk(annotation):
            if isinstance(opaque, ast.Subscript):
                port_match = runtime.same_name(
                    port, runtime.resolve_symbol(scope, opaque.value)
                )
                u.Cli.info(
                    f"mod: opaque-port annotation={ast.unparse(opaque.value)} "
                    f"port={port_match} "
                    f"origin={cls._identity(scope, opaque.value)}"
                )
            if not isinstance(opaque, ast.Subscript) or not runtime.same_name(
                port, runtime.resolve_symbol(scope, opaque.value)
            ):
                continue
            for collection in ast.walk(opaque.slice):
                if (
                    not isinstance(collection, ast.Subscript)
                    or cls._identity(scope, collection.value) not in mutable
                ):
                    continue
                offsets.extend(
                    runtime.source_offset(module.source_code, node)
                    for node in ast.walk(collection.slice)
                    if isinstance(node, ast.Name | ast.Attribute)
                    and cls._identity(scope, node) == concrete
                )
        return (module, tuple(offsets)) if offsets else None

    @classmethod
    def opaque_port_changes(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        resources: Sequence[p.Infra.RopeResource],
        issues: Sequence[p.Infra.Issue],
        routes: Mapping[str, str],
    ) -> list[p.Infra.RopeChangeContents]:
        """Restructure only opaque fields linked to a diagnosed returning mutator.

        Returns:
            Native Rope changes, retaining every serialized payload annotation.

        Raises:
            ValueError: If ``resource is None``.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        twins = cls._twins(project, routes)
        admitted = {
            Path(resource.real_path).resolve(): resource for resource in resources
        }
        candidates: dict[tuple[Path, int], tuple[str, str]] = {}
        for issue in issues:
            path = Path(issue.file)
            path = path if path.is_absolute() else Path(project.root.real_path) / path
            if (
                issue.code not in {"unsupported-operation", "bad-argument-type"}
                or path not in admitted
            ):
                if issue.code == "unsupported-operation":
                    u.Cli.info(
                        f"mod: opaque-port diagnostic outside source scope: {path}"
                    )
                continue
            module = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
                project.get_pymodule(admitted[path])
            )
            proof = (
                cls._proof(module, issue, twins)
                if issue.code == "unsupported-operation"
                else cls._argument_proof(project, module, issue, twins)
            )
            selected = (
                None if proof is None else cls._field_matches(project, proof, twins)
            )
            u.Cli.info(
                f"mod: opaque-port diagnostic={path}:{issue.line} "
                f"mutator={None if proof is None else proof[1:]} "
                f"opaque_field={selected is not None}"
            )
            if selected is None or proof is None:
                continue
            declaration, offsets = selected
            resource = declaration.get_resource()
            if resource is None:
                message = f"{rule.id}: opaque field has no native source resource"
                raise ValueError(message)
            origin = Path(resource.real_path).resolve()
            if origin not in admitted:
                continue
            for offset in offsets:
                candidates[origin, offset] = (
                    runtime.native_object_identity(twins[proof[2]][0]).replace(
                        "::", "."
                    ),
                    twins[proof[2]][1],
                )
        return cls._native_changes(project, rule, admitted, candidates)

    @staticmethod
    def _native_changes(
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        admitted: Mapping[Path, p.Infra.RopeResource],
        candidates: Mapping[tuple[Path, int], tuple[str, str]],
    ) -> list[p.Infra.RopeChangeContents]:
        changes: dict[Path, p.Infra.RopeChangeContents] = {}
        for (path, offset), (model, protocol) in sorted(
            candidates.items(), reverse=True
        ):
            plans = FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
                Path(project.root.real_path),
                (),
                {origin: change.new_contents for origin, change in changes.items()},
                source_project=project,
            )
            with project.source_view(
                declared_files=plans, additional_source_folders=None
            ):
                native = FlextInfraUtilitiesRopeRuntimeRefactors.restructure_changes(
                    project,
                    m.Infra.RopeRestructureRequest(
                        pattern=rule.pattern,
                        goal=protocol,
                        arguments={"model": "name=" + model},
                        resources=(admitted[path],),
                        match_filter=lambda _module, match, offset=offset: (
                            match.get_region()[0] == offset
                        ),
                    ),
                )
                members = FlextInfraUtilitiesRopeRuntimeRefactors.change_set_members(
                    native.changes, f"{rule.id}: invalid native opaque-port changes"
                ).unwrap()
                if len(members) != 1:
                    message = (
                        f"{rule.id}: native change lost its admitted source: {path}"
                    )
                    raise ValueError(message)
                changes[path] = members[0]
        return list(changes.values())


__all__: list[str] = ["FlextInfraUtilitiesSemanticOpaquePorts"]
