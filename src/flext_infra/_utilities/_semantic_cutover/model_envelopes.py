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
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery
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
    def _source_identity(
        project: p.Infra.RopeProject, value: p.Infra.RopePyObject
    ) -> str:
        """Keep the native declaration under its authenticated source module."""
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        if isinstance(value, p.Infra.RopeSourceClass):
            module = FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                value.get_module(), source_project=project
            )
            return (
                f"{module}.{runtime.native_object_identity(value).partition('::')[2]}"
            )
        return runtime.native_object_identity(value).replace("::", ".")

    @classmethod
    def _projected_twins(
        cls, project: p.Infra.RopeProject, routes: Mapping[str, str]
    ) -> Mapping[str, str]:
        """Read each model's protocol from its owning package's source inventory."""
        from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
        from flext_infra._utilities.protocol_models import (
            FlextInfraUtilitiesModelsProtocol,
        )

        runtime = FlextInfraUtilitiesRopeRuntimeModules
        roots: dict[Path, set[Path]] = {}
        for model in routes:
            if model.startswith("m."):
                continue
            concrete = runtime.qualified_name(project, model).get_object()
            if not isinstance(concrete, p.Infra.RopeSourceClass):
                continue
            resource = concrete.get_module().get_resource()
            if resource is not None:
                root = FlextInfraUtilitiesDiscovery.project_root(
                    Path(resource.real_path), source_project=project
                )
                if root is not None:
                    roots.setdefault(root, set()).add(Path(resource.real_path))
        twins: dict[str, str] = {}
        for root in sorted(roots):
            for (
                package
            ) in FlextInfraUtilitiesModelsProtocol.protocol_model_package_names(
                root, project
            ):
                projection = FlextInfraUtilitiesModelsProtocol._ModelProtocolProjection(
                    root, project, package_name=package
                )
                layout = projection.source_layout()
                if layout is None or not any(
                    path.is_relative_to(layout[0]) for path in roots[root]
                ):
                    continue
                if projection.source_model_inventory() is None:
                    continue
                for model in projection.source_model_protocols:
                    protocol = projection.source_model_protocol_routes.get(model)
                    if protocol is None or routes.get(model) != protocol:
                        continue
                    concrete = runtime.qualified_name(project, model).get_object()
                    target = runtime.qualified_name(
                        project, f"{package}.{protocol}"
                    ).get_object()
                    twins[cls._source_identity(project, concrete)] = (
                        cls._source_identity(project, target)
                    )
        return twins

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
        twins: Mapping[str, str],
        bindings: tuple[p.Infra.RopeSourceClass, p.Infra.RopeScope, str, ast.expr],
    ) -> bool:
        """Authenticate protocol substitutions through generated source bindings.

        Returns:
            Whether the types differ only by an authenticated projected model.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        field = runtime.expression_name(bindings[0].get_scope(), bindings[2])
        if field is None:
            return False
        owner, line = runtime.definition_location(field)
        if owner is None or line is None:
            return False
        field_scope = owner.get_scope().get_inner_scope_for_line(line)
        expressions = tuple(
            runtime.build_string_module(project, value).get_ast().body[0]
            for value in types
        )
        if not all(isinstance(value, ast.Expr) for value in expressions):
            return False
        supplied, requested = (
            value.value for value in expressions if isinstance(value, ast.Expr)
        )
        accepted, changed = cls._annotation_match(
            project,
            (supplied, requested),
            (bindings[1], field_scope),
            twins,
            cls._argument_origin(project, bindings[3], bindings[1]),
        )
        return accepted and changed

    @staticmethod
    def _argument_origin(
        project: p.Infra.RopeProject,
        expression: ast.expr,
        scope: p.Infra.RopeScope,
    ) -> p.Infra.RopePyObject | None:
        """Retain the native annotation owner behind a diagnosed container alias.

        Returns:
            Its original native outer type, or None without declaration proof.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        origin = None
        if isinstance(expression, ast.Name | ast.Attribute):
            binding = runtime.resolve_symbol(scope, expression)
            declared = (
                None
                if binding is None
                else runtime.annotation_assignment_outer_type(project, binding)
            )
            origin = None if declared is None else declared[0]
        elif isinstance(expression, ast.Call):
            binding = runtime.resolve_symbol(scope, expression.func)
            function = None if binding is None else binding.get_object()
            if function is not None and FlextInfraUtilitiesRopeRuntimeTypes.py_function(
                function
            ):
                returns = function.get_ast().returns
                if returns is not None:
                    origin = runtime.annotation_origin(
                        project, returns, function.get_scope()
                    )
        alias = None if origin is None else runtime.annotation_alias_definition(origin)
        if alias is not None:
            origin = runtime.annotation_origin(project, alias[0].value, alias[1])
        return None if origin is None else origin.get_object()

    @classmethod
    def _atom_identity(
        cls,
        project: p.Infra.RopeProject,
        expression: ast.expr,
        scope: p.Infra.RopeScope,
        twins: Mapping[str, str],
    ) -> str:
        """Resolve diagnostic names at their native lexical declaration.

        Returns:
            The original source identity, or empty without a native binding.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        text = ast.unparse(expression)
        if text in twins or text in twins.values():
            return text
        bound = runtime.expression_name(scope, text)
        return (
            "" if bound is None else cls._source_identity(project, bound.get_object())
        )

    @classmethod
    def _annotation_match(
        cls,
        project: p.Infra.RopeProject,
        expressions: tuple[ast.expr, ast.expr],
        scopes: tuple[p.Infra.RopeScope, p.Infra.RopeScope],
        twins: Mapping[str, str],
        actual_origin: p.Infra.RopePyObject | None = None,
    ) -> tuple[bool, bool]:
        """Prove compatibility and an actual model/protocol difference.

        Returns:
            Whether the shape is accepted and contains a proved protocol twin.

        """
        supplied, requested = expressions
        if ast.dump(supplied) == ast.dump(requested):
            return True, False
        if isinstance(supplied, ast.BinOp) and isinstance(supplied.op, ast.BitOr):
            matches = tuple(
                cls._annotation_match(project, (member, requested), scopes, twins)
                for member in (supplied.left, supplied.right)
            )
            return all(item[0] for item in matches), any(item[1] for item in matches)
        if isinstance(requested, ast.BinOp) and isinstance(requested.op, ast.BitOr):
            matches = tuple(
                cls._annotation_match(project, (supplied, member), scopes, twins)
                for member in (requested.left, requested.right)
            )
            return any(item[0] for item in matches), any(
                item[0] and item[1] for item in matches
            )
        if isinstance(supplied, ast.Subscript) and isinstance(requested, ast.Subscript):
            return cls._container_match(
                project, (supplied, requested), scopes, twins, actual_origin
            )
        if not isinstance(supplied, ast.Name | ast.Attribute) or not isinstance(
            requested, ast.Name | ast.Attribute
        ):
            return False, False
        expected = cls._atom_identity(project, requested, scopes[1], twins)
        actual = cls._atom_identity(project, supplied, scopes[0], twins)
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        if not actual and expected in twins:
            origin = runtime.qualified_name(project, twins[expected]).get_object()
            if FlextInfraUtilitiesRopeRuntimeTypes.py_class(origin):
                actual = cls._atom_identity(
                    project, supplied, origin.get_scope(), twins
                )
        return bool(actual) and actual in {expected, twins.get(expected)}, (
            expected in twins and actual == twins[expected]
        )

    @classmethod
    def _container_match(
        cls,
        project: p.Infra.RopeProject,
        expressions: tuple[ast.Subscript, ast.Subscript],
        scopes: tuple[p.Infra.RopeScope, p.Infra.RopeScope],
        twins: Mapping[str, str],
        actual_origin: p.Infra.RopePyObject | None,
    ) -> tuple[bool, bool]:
        """Use native collection identities and their real covariance contract.

        Returns:
            Whether the collection is accepted and carries a protocol twin.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        supplied, requested = expressions
        origins = {
            name: runtime.native_object_identity(
                runtime.qualified_name(project, name).get_object()
            ).replace("::", ".")
            for name in (
                "builtins.dict",
                "builtins.list",
                "builtins.tuple",
                "collections.abc.Mapping",
                "collections.abc.MutableMapping",
                "collections.abc.Sequence",
                "collections.abc.MutableSequence",
            )
        }
        actual = cls._atom_identity(project, supplied.value, scopes[0], twins)
        if actual_origin is not None:
            actual = (
                runtime.native_object_identity(actual_origin).replace("::", ".")
                or actual
            )
        expected = cls._atom_identity(project, requested.value, scopes[1], twins)
        source = (
            list(supplied.slice.elts)
            if isinstance(supplied.slice, ast.Tuple)
            else [supplied.slice]
        )
        target = (
            list(requested.slice.elts)
            if isinstance(requested.slice, ast.Tuple)
            else [requested.slice]
        )
        if expected == origins["collections.abc.Sequence"]:
            admitted = {
                origins[name]
                for name in (
                    "builtins.list",
                    "builtins.tuple",
                    "collections.abc.Sequence",
                    "collections.abc.MutableSequence",
                )
            }
            if actual not in admitted or len(target) != 1:
                return False, False
            source = cls._variadic_items(source)
            target *= len(source)
        elif expected == origins["collections.abc.Mapping"]:
            if (
                actual
                not in {
                    origins[name]
                    for name in (
                        "builtins.dict",
                        "collections.abc.Mapping",
                        "collections.abc.MutableMapping",
                    )
                }
                or not cls._mapping_arity(source, target)
                or cls._annotation_match(project, (source[0], target[0]), scopes, twins)
                != (True, False)
            ):
                return False, False
        elif actual == expected == origins["builtins.tuple"]:
            match target:
                case [element, ast.Constant(value=variadic)] if variadic is Ellipsis:
                    source = cls._variadic_items(source)
                    target = [element] * len(source)
                case _:
                    pass
        elif actual != expected or actual not in {
            origins["builtins.dict"],
            origins["builtins.list"],
        }:
            return False, False
        if len(source) != len(target):
            return False, False
        matches = tuple(
            cls._annotation_match(project, pair, scopes, twins)
            for pair in zip(source, target, strict=True)
        )
        return all(item[0] for item in matches), any(item[1] for item in matches)

    @staticmethod
    def _variadic_items(items: list[ast.expr]) -> list[ast.expr]:
        """Read the native variadic tuple form without treating Ellipsis as a type.

        Returns:
            One repeated type or the original fixed members.

        """
        match items:
            case [element, ast.Constant(value=variadic)] if variadic is Ellipsis:
                return [element]
            case _:
                return items

    @staticmethod
    def _mapping_arity(source: list[ast.expr], target: list[ast.expr]) -> bool:
        """Retain exactly one key and value for a native mapping annotation.

        Returns:
            Whether both collections have the native key/value arity.

        """
        match source, target:
            case [_, _], [_, _]:
                return True
            case _:
                return False

    @classmethod
    def _model_envelope_issues(
        cls,
        project: p.Infra.RopeProject,
        issues: Sequence[p.Infra.Issue],
    ) -> Mapping[Path, tuple[Sequence[_Diagnostic], Sequence[p.Infra.Issue]]]:
        """Retain diagnostics whose type difference has a source-owned twin.

        Returns:
            Native argument diagnostics grouped by logical source identity.

        """
        root = Path(project.root.real_path)
        admitted: dict[
            Path,
            tuple[
                list[FlextInfraUtilitiesSemanticModelEnvelopes._Diagnostic],
                list[p.Infra.Issue],
            ],
        ] = {}
        for issue in issues:
            path = Path(issue.file)
            path = path if path.is_absolute() else root / path
            rows = admitted.setdefault(path, ([], []))
            rows[1].append(issue)
            pair = cls._diagnostic_pair(issue)
            if pair is None:
                continue
            if not pair[-1].endswith(".__init__"):
                continue
            rows[0].append(cls._Diagnostic(issue, *pair))
        return admitted

    @classmethod
    def _model_envelope_call(
        cls,
        module: p.Infra.RopePyModule,
        invocation: ast.Call,
        findings: Sequence[_Diagnostic],
        context: tuple[
            p.Infra.RopeProject,
            p.Infra.RopePyObject,
            Mapping[str, str],
            Sequence[p.Infra.Issue],
        ],
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
            or invocation.end_lineno is None
            or invocation.end_col_offset is None
        ):
            return False
        if any(
            (invocation.lineno, invocation.col_offset + 1)
            <= (issue.line, issue.column)
            <= (invocation.end_lineno, invocation.end_col_offset + 1)
            and not any(issue is finding.issue for finding in located)
            for issue in context[3]
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
        constructor = f"{cls._source_identity(context[0], model)}.__init__"
        declaration_scope = model.get_scope().parent
        # One protocol-valued field cannot admit an unrelated invalid keyword.
        accepted = all(
            (
                constructor == finding.constructor
                or (
                    declaration_scope is not None
                    and runtime.same_name(
                        binding,
                        runtime.expression_name(
                            declaration_scope,
                            finding.constructor.removesuffix(".__init__"),
                        ),
                    )
                )
            )
            and cls._protocol_twin(
                context[0],
                (finding.actual, finding.expected),
                context[2],
                (
                    model,
                    scope,
                    finding.parameter,
                    next(
                        keyword.value
                        for keyword in invocation.keywords
                        if keyword.arg == finding.parameter
                    ),
                ),
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
        twins = cls._projected_twins(project, routes)

        updates: dict[Path, str] = {}
        planned: dict[Path, p.Infra.RopeChangeContents] = {}
        for resource in resources:
            path = Path(resource.real_path)
            if path not in admitted or not admitted[path][0]:
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
                        module,
                        node,
                        admitted[path][0],
                        (project, model_base, twins, admitted[path][1]),
                    )
                ),
                key=lambda node: runtime.source_offset(module.source_code, node),
                reverse=True,
            )
            u.Cli.info(
                f"mod: model-envelope source={path} "
                f"diagnostics={len(admitted[path][0])} "
                f"admitted_calls={len(invocations)}"
            )
            for invocation in invocations:
                offset = runtime.source_offset(module.source_code, invocation)
                change = cls._native_envelope_change(
                    project, rules, resource, (offset, invocation), updates
                )
                planned[path] = change
                updates[path] = change.new_contents
        return list(planned.values())
