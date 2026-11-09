"""Admit native model-envelope refactorings from source-bound Pyrefly findings.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import NamedTuple

from flext_cli import u

from flext_infra import m, p
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._semantic_cutover.declaration_payload import (
    FlextInfraUtilitiesDeclarationPayload,
)
from flext_infra._utilities.workspace_snapshot import (
    FlextInfraUtilitiesWorkspaceSnapshot,
)


class FlextInfraUtilitiesSemanticModelEnvelopes:
    """Keep valid native constructors while correcting proven protocol boundaries."""

    class _Diagnostic(NamedTuple):
        """Native analyzer facts parsed once at the diagnostic boundary."""

        issue: p.Infra.Issue
        actual: str
        parameter: str
        expected: str
        constructor: str

    @staticmethod
    def _diagnostic_pair(issue: p.Infra.Issue) -> tuple[str, str, str, str] | None:
        """Read only Pyrefly's exact native argument diagnostic shape.

        Returns:
            Actual type, parameter, required type and constructor identity.

        """
        if issue.code != "bad-argument-type":
            return None
        parts = issue.message.split("`")
        shape = [
            "Argument ",
            " is not assignable to parameter ",
            " with type ",
            " in function ",
            "",
        ]
        if parts[::2] != shape or len(parts[1::2]) != len(shape) - 1:
            return None
        return parts[1], parts[3], parts[5], parts[7]

    @classmethod
    def _protocol_twin(
        cls,
        project: p.Infra.RopeProject,
        types: tuple[str, str],
        routes: Mapping[str, str],
        bindings: tuple[p.Infra.RopeSourceClass, p.Infra.RopeScope, str],
    ) -> bool:
        """Authenticate protocol substitutions through generated source bindings.

        Returns:
            Whether the types differ only by an authenticated projected model.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        actual, expected = types
        replaced = expected
        for model, protocol in routes.items():
            if model.startswith("m.") or model not in replaced:
                continue
            concrete = runtime.qualified_name(project, model).get_object()
            identity = runtime.native_object_identity(concrete).replace("::", ".")
            if identity != model:
                continue
            target = runtime.qualified_name(
                project, f"{model.partition('.')[0]}.{protocol}"
            ).get_object()
            projected = runtime.native_object_identity(target).replace("::", ".")
            if projected:
                replaced = replaced.replace(identity, projected)
        return replaced != expected and (
            replaced == actual
            or cls._covariant_argument(project, (actual, replaced), bindings)
        )

    @classmethod
    def _covariant_argument(
        cls,
        project: p.Infra.RopeProject,
        types: tuple[str, str],
        bindings: tuple[p.Infra.RopeSourceClass, p.Infra.RopeScope, str],
    ) -> bool:
        """Use native syntax, field bindings and builtin Sequence membership.

        Returns:
            Whether an optional member or a proved Sequence accepts the value.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        expressions = tuple(
            runtime.build_string_module(project, value).get_ast().body[0]
            for value in types
        )
        if not all(isinstance(value, ast.Expr) for value in expressions):
            return False
        supplied, requested = (
            value.value for value in expressions if isinstance(value, ast.Expr)
        )
        if isinstance(requested, ast.BinOp) and isinstance(requested.op, ast.BitOr):
            if (
                isinstance(requested.right, ast.Constant)
                and requested.right.value is None
            ):
                requested = requested.left
            elif (
                isinstance(requested.left, ast.Constant)
                and requested.left.value is None
            ):
                requested = requested.right
        if ast.dump(supplied) == ast.dump(requested) or cls._fixed_tuple_matches(
            project, types[0], ast.unparse(requested)
        ):
            return True
        if not isinstance(supplied, ast.Subscript) or not isinstance(
            requested, ast.Subscript
        ):
            return False
        field = runtime.expression_name(bindings[0].get_scope(), bindings[2])
        if field is None:
            return False
        owner, line = field.get_definition_location()
        if owner is None or line is None:
            return False
        scope = owner.get_scope().get_inner_scope_for_line(line)
        return cls._sequence_argument(
            project, (supplied, requested), (bindings[1], scope)
        )

    @staticmethod
    def _sequence_argument(
        project: p.Infra.RopeProject,
        expressions: tuple[ast.Subscript, ast.Subscript],
        scopes: tuple[p.Infra.RopeScope, p.Infra.RopeScope],
    ) -> bool:
        """Prove stdlib Sequence identity and each supplied element contract.

        Returns:
            Whether native list or tuple elements satisfy this Sequence field.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        supplied, requested = expressions
        expected = runtime.resolve_symbol(scopes[1], requested.value)
        if not runtime.same_name(
            runtime.qualified_name(project, "collections.abc.Sequence"), expected
        ):
            return False
        actual = runtime.resolve_symbol(scopes[0], supplied.value)
        if runtime.same_name(runtime.qualified_name(project, "builtins.list"), actual):
            return issubclass(list, Sequence) and ast.dump(supplied.slice) == ast.dump(
                requested.slice
            )
        if not runtime.same_name(
            runtime.qualified_name(project, "builtins.tuple"), actual
        ) or not issubclass(tuple, Sequence):
            return False
        items = (
            supplied.slice.elts
            if isinstance(supplied.slice, ast.Tuple)
            else [supplied.slice]
        )
        match items:
            case [element, ast.Constant(value=variadic)] if variadic is Ellipsis:
                items = [element]
            case _:
                pass
        return all(ast.dump(item) == ast.dump(requested.slice) for item in items)

    @staticmethod
    def _fixed_tuple_matches(
        project: p.Infra.RopeProject, actual: str, expected: str
    ) -> bool:
        """Admit only fixed homogeneous tuples of an authenticated protocol twin.

        Returns:
            Whether native tuple identity and every fixed element match.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        if not all(value.startswith("tuple[") for value in (actual, expected)):
            return False
        provided = runtime.build_string_module(project, actual)
        required = runtime.build_string_module(project, expected)
        expressions: list[ast.Subscript] = []
        container = runtime.qualified_name(project, "builtins.tuple")
        for module in (provided, required):
            statement = module.get_ast().body[0]
            if not isinstance(statement, ast.Expr) or not isinstance(
                statement.value, ast.Subscript
            ):
                return False
            expression = statement.value
            if not runtime.same_name(
                container, runtime.resolve_symbol(module.get_scope(), expression.value)
            ):
                return False
            expressions.append(expression)
        supplied, requested = expressions
        match requested.slice:
            case ast.Tuple(elts=[element, ast.Constant(value=variadic)]) if (
                variadic is Ellipsis
            ):
                items = (
                    supplied.slice.elts
                    if isinstance(supplied.slice, ast.Tuple)
                    else (supplied.slice,)
                )
                return all(ast.dump(item) == ast.dump(element) for item in items)
            case _:
                return False

    @classmethod
    def _model_envelope_issues(
        cls,
        project: p.Infra.RopeProject,
        issues: Sequence[p.Infra.Issue],
    ) -> Mapping[Path, Sequence[_Diagnostic]]:
        """Retain diagnostics whose type difference has a source-owned twin.

        Returns:
            Native argument diagnostics grouped by logical source identity.

        """
        root = Path(project.root.real_path)
        admitted: dict[
            Path, list[FlextInfraUtilitiesSemanticModelEnvelopes._Diagnostic]
        ] = {}
        for issue in issues:
            pair = cls._diagnostic_pair(issue)
            if pair is None:
                continue
            if not pair[-1].endswith(".__init__"):
                continue
            path = Path(issue.file)
            path = path if path.is_absolute() else root / path
            admitted.setdefault(path, []).append(cls._Diagnostic(issue, *pair))
        return admitted

    @classmethod
    def _model_envelope_call(
        cls,
        module: p.Infra.RopePyModule,
        invocation: ast.Call,
        findings: Sequence[_Diagnostic],
        context: tuple[p.Infra.RopeProject, p.Infra.RopePyObject, Mapping[str, str]],
    ) -> bool:
        """Prove the native constructor and its diagnosed keyword.

        Returns:
            Whether this exact call is a native model-envelope boundary.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        located = tuple(
            finding
            for finding in findings
            if any(
                keyword.arg == finding.parameter
                and (keyword.value.lineno, keyword.value.col_offset + 1)
                <= (finding.issue.line, finding.issue.column)
                <= (keyword.value.end_lineno, keyword.value.end_col_offset + 1)
                for keyword in invocation.keywords
                if keyword.value.end_lineno is not None
                and keyword.value.end_col_offset is not None
            )
        )
        if (
            not located
            or invocation.args
            or any(keyword.arg is None for keyword in invocation.keywords)
        ):
            return False
        scope = runtime.scope_at(
            module, runtime.source_offset(module.source_code, invocation)
        )
        binding = runtime.resolve_symbol(scope, invocation.func)
        if (
            binding is None
            or not isinstance(model := binding.get_object(), p.Infra.RopeSourceClass)
            or context[1]
            not in FlextInfraUtilitiesDeclarationPayload.class_ancestry(model)
        ):
            return False
        module_name, _separator, qualified = runtime.native_object_identity(
            binding.get_object()
        ).partition("::")
        constructor = f"{module_name}.{qualified.rpartition('.')[2]}.__init__"
        accepted = any(
            constructor == finding.constructor
            and cls._protocol_twin(
                context[0],
                (finding.actual, finding.expected),
                context[2],
                (model, scope, finding.parameter),
            )
            for finding in located
        )
        u.Cli.info(
            f"mod: model-envelope candidate={module.get_name()}:{invocation.lineno} "
            f"native_constructor={constructor} "
            f"diagnosed={tuple(finding.constructor for finding in located)} "
            f"admitted={accepted}"
        )
        return accepted

    @staticmethod
    def _native_envelope_change(
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        resource: p.Infra.RopeResource,
        occurrence: tuple[int, ast.Call],
        updates: Mapping[Path, str],
    ) -> p.Infra.RopeChangeContents:
        """Specialize the native call shape and let Rope retain every expression.

        Returns:
            The native content change for the authenticated call.

        Raises:
            ValueError: Native matching lost the source admitted by the analyzer.

        """
        offset, invocation = occurrence
        captures = ", ".join(
            f"{keyword.arg}=${{argument_{index}}}"
            for index, keyword in enumerate(invocation.keywords)
        )
        values = ", ".join(
            f'"{keyword.arg}": (${{argument_{index}}})'
            for index, keyword in enumerate(invocation.keywords)
        )
        with project.source_view(
            declared_files=FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
                Path(project.root.real_path), (), updates, source_project=project
            ),
            additional_source_folders=None,
        ) as candidate:
            changes = FlextInfraUtilitiesRopeRuntimeRefactors.restructure_changes(
                candidate,
                m.Infra.RopeRestructureRequest(
                    pattern=rule.pattern.replace("${arguments}", captures),
                    goal=rule.goal.replace("${arguments}", values),
                    arguments=rule.arguments,
                    resources=(resource,),
                    match_filter=lambda _module, match: match.get_region()[0] == offset,
                ),
            )
            members = FlextInfraUtilitiesRopeRuntimeRefactors.change_set_members(
                changes.changes, f"{rule.id}: invalid native envelope changes"
            ).unwrap()
            if len(members) != 1:
                message = (
                    f"{rule.id}: native envelope change lost its admitted "
                    f"source: {resource.real_path}:{invocation.lineno}"
                )
                raise ValueError(message)
            return members[0]

    @classmethod
    def model_envelope_changes(
        cls,
        project: p.Infra.RopeProject,
        rules: p.Infra.RopeContractRule,
        resources: Sequence[p.Infra.RopeResource],
        issues: Sequence[p.Infra.Issue],
        routes: Mapping[str, str],
    ) -> list[p.Infra.RopeChangeContents]:
        """Delegate admitted keyword shapes to native Rope in reverse source order.

        Returns:
            Native content plans; no source is written by this operation.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        model_base = runtime.qualified_name(project, "pydantic.BaseModel").get_object()
        admitted = cls._model_envelope_issues(project, issues)

        updates: dict[Path, str] = {}
        planned: dict[Path, p.Infra.RopeChangeContents] = {}
        for resource in resources:
            path = Path(resource.real_path)
            if path not in admitted:
                continue
            module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                project,
                FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                    resource, path
                ),
            )
            invocations = sorted(
                (
                    node
                    for node in ast.walk(module.get_ast())
                    if isinstance(node, ast.Call)
                    and cls._model_envelope_call(
                        module, node, admitted[path], (project, model_base, routes)
                    )
                ),
                key=lambda node: runtime.source_offset(module.source_code, node),
                reverse=True,
            )
            u.Cli.info(
                f"mod: model-envelope source={path} "
                f"diagnostics={len(admitted[path])} admitted_calls={len(invocations)}"
            )
            for invocation in invocations:
                offset = runtime.source_offset(module.source_code, invocation)
                change = cls._native_envelope_change(
                    project, rules, resource, (offset, invocation), updates
                )
                planned[path] = change
                updates[path] = change.new_contents
        return list(planned.values())
