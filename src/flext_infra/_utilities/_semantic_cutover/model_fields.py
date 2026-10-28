"""Prove native field metadata and narrow untrusted model-class boundaries.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_infra import c
from flext_infra._utilities._codemod import FlextInfraUtilitiesCodemodProject
from flext_infra._utilities._rope.rope_module_patch import (
    FlextInfraUtilitiesRopeModulePatch,
)
from flext_infra._utilities._rope.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._rope.rope_runtime_refactors import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities._rope.rope_runtime_types import (
    FlextInfraUtilitiesTypesRopeRuntime,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverEdits,
    FlextInfraUtilitiesSemanticCutoverModelFieldsBindings,
)

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, p, t


class FlextInfraUtilitiesSemanticCutoverModelFields(
    FlextInfraUtilitiesSemanticCutoverEdits,
    FlextInfraUtilitiesSemanticCutoverModelFieldsBindings,
):
    """Keep existing invalid-input errors while proving model-class identity."""

    @staticmethod
    def _contract_arguments(
        rule: p.Infra.RopeContractRule,
    ) -> Mapping[str, str | Sequence[str]]:
        """Constrain ordinary captures before native call admission.

        Returns:
            The argument constraints that remain applicable to the native call.

        Raises:
            ValueError: If an ownership transfer lacks one native receiver constraint.

        """
        if rule.ownership_transfer is not None:
            if len(rule.arguments) != 1 or not all(
                isinstance(value, str) and value.startswith("name=")
                for value in rule.arguments.values()
            ):
                msg = (
                    f"{rule.id}: ownership transfer requires "
                    "one native receiver constraint"
                )
                raise ValueError(msg)
            return {}
        if rule.required_field:
            return {
                name: constraint
                for name, constraint in rule.arguments.items()
                if name != rule.call_target
            }
        return rule.arguments

    @staticmethod
    def _admitted_field_metadata(
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
    ) -> bool:
        """Prove native model metadata without evaluating authored expressions.

        Returns:
            Whether the captured field metadata satisfies the native rule.

        Raises:
            ValueError: If the native field metadata has no original callee AST.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        tree = module.get_ast()
        if rule.call_target is None or not isinstance(tree, ast.AST):
            msg = f"{rule.id}: native field metadata has no original callee AST"
            raise ValueError(msg)
        captured = match.get_ast(rule.call_target)
        invocation = (
            captured
            if isinstance(captured, ast.Call)
            else next(
                (
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and node.func is captured
                ),
                None,
            )
        )
        constraint = rule.arguments.get(rule.call_target)
        if (
            invocation is None
            or constraint is None
            or not FlextInfraUtilitiesRopeRuntimeRefactors.semantic_capture(
                project, module, invocation.func, constraint, name=rule.call_target
            )
        ):
            return False
        declaration = next(
            (
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.AnnAssign) and node.value is invocation
            ),
            None,
        )
        if declaration is None or not isinstance(declaration.target, ast.Name):
            return False
        annotation = declaration.annotation
        if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
            annotation = ast.parse(annotation.value, mode="eval").body
        scope = runtime.scope_at(module, match.get_region()[0])
        classvar = runtime.qualified_name(project, "typing.ClassVar")
        if any(
            runtime.same_name(classvar, runtime.resolve_symbol(scope, node))
            for node in ast.walk(annotation)
            if isinstance(node, c.Infra.AST_NAME_REFERENCE_TYPES)
        ):
            return False
        name = declaration.target.id
        if rule.private_attribute:
            return (
                name.startswith("_")
                and not name.startswith("__")
                and not invocation.args
                and not invocation.keywords
            )
        if name.startswith("_"):
            return False
        return (
            FlextInfraUtilitiesSemanticCutoverModelFields._concrete_field_default(
                invocation
            )
            and len(
                FlextInfraUtilitiesSemanticCutoverModelFields._field_reordered_calls(
                    project, rule, module, match
                )
            )
            == 1
            if rule.defaulted_field
            else (
                len(invocation.args) <= 1
                and all(
                    isinstance(argument, ast.Constant) and argument.value is Ellipsis
                    for argument in invocation.args
                )
                and all(
                    keyword.arg is not None
                    and (
                        keyword.arg not in {"default", "default_factory"}
                        or (
                            isinstance(keyword.value, ast.Constant)
                            and (
                                (
                                    keyword.arg == "default"
                                    and keyword.value.value is Ellipsis
                                )
                                or (
                                    keyword.arg == "default_factory"
                                    and keyword.value.value is None
                                )
                            )
                        )
                    )
                    for keyword in invocation.keywords
                )
            )
        )

    @staticmethod
    def _concrete_field_default(invocation: ast.Call) -> bool:
        """Admit exactly one explicit concrete default, never a factory.

        Returns:
            Whether extraction preserves an explicit, unambiguous native default.

        """
        defaults = [
            *invocation.args,
            *(
                keyword.value
                for keyword in invocation.keywords
                if keyword.arg == "default"
            ),
        ]
        return (
            len(defaults) == 1
            and not isinstance(defaults[0], ast.Starred)
            and not (
                isinstance(defaults[0], ast.Constant) and defaults[0].value is Ellipsis
            )
            and all(
                keyword.arg is not None and keyword.arg != "default_factory"
                for keyword in invocation.keywords
            )
        )

    @classmethod
    def _field_contract_templates(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        resources: Sequence[p.Infra.RopeResource],
    ) -> Sequence[tuple[str, str]]:
        """Specialize explicit argument shapes, leaving matching/writing to Rope.

        Returns:
            Native pattern/goal pairs retaining each metadata keyword capture.

        """
        if not rule.defaulted_field:
            return ((rule.pattern, rule.goal),)
        templates: MutableMapping[tuple[str, str], None] = {}
        field = f"${{{rule.call_target}}}"
        default = f"${{{rule.value_default}}}"
        for resource in resources:
            module = project.get_pymodule(resource)
            tree = module.get_ast()
            if not isinstance(tree, ast.AST):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.AnnAssign) or not isinstance(
                    node.value, ast.Call
                ):
                    continue
                call = node.value
                if not cls._concrete_field_default(call):
                    continue
                arguments = [default] if call.args else []
                metadata: list[str] = []
                for index, keyword in enumerate(call.keywords):
                    if keyword.arg == "default":
                        arguments.append(f"default={default}")
                    else:
                        captured = f"{keyword.arg}=${{metadata_{index}}}"
                        arguments.append(captured)
                        metadata.append(captured)
                pattern = rule.pattern.replace(
                    f"{field}({default})", field + "(" + ", ".join(arguments) + ")"
                )
                goal = rule.goal.replace(
                    f"{field}()", field + "(" + ", ".join(metadata) + ")"
                )
                templates[pattern, goal] = None
        return tuple(templates)

    @classmethod
    def _field_reordered_calls(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
    ) -> Sequence[tuple[int, int]]:
        """Retain every call lacking an exact native evaluation-safety proof.

        Returns:
            Calls whose evaluation moves into the field annotation.

        """
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        calls = refactors.word_call_regions(module.source_code, match.get_region())
        if rule.defaulted_field and rule.value_default is not None:
            begin, end = refactors.semantic_capture_region(match, rule.value_default)
            calls = tuple(
                region for region in calls if not begin <= region[0] < region[1] <= end
            )
        if rule.required_field:
            pure = cls._pure_field_factory_metadata(project, rule, module, match)
            calls = tuple(
                region
                for region in calls
                if not any(begin <= region[0] < region[1] <= end for begin, end in pure)
            )
        return calls

    @classmethod
    def _pure_field_factory_metadata(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
    ) -> Sequence[tuple[int, int]]:
        """Prove direct SDK metadata that only stores a deferred builtin factory.

        Returns:
            Pure metadata-call regions whose relative evaluation is unobservable.

        """
        contract = match.get_ast("contract")
        if not isinstance(contract, ast.AST):
            return ()
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        scope = runtime.scope_at(module, match.get_region()[0])
        annotated = runtime.qualified_name(project, "typing.Annotated")
        regions: list[tuple[int, int]] = []
        for node in ast.walk(contract):
            if not isinstance(node, ast.Subscript) or not isinstance(
                node.slice, ast.Tuple
            ):
                continue
            if not runtime.same_name(
                annotated, runtime.resolve_symbol(scope, node.value)
            ):
                continue
            reference = ast.unparse(node.value)
            if not all(
                FlextInfraUtilitiesCodemodProject.single_reaching_binding(
                    module, scope, name, runtime.source_offset(module.source_code, node)
                )
                for name in dict.fromkeys((reference.partition(".")[0], reference))
            ):
                continue
            for metadata in node.slice.elts[1:]:
                if not isinstance(
                    metadata, ast.Call
                ) or not cls._pure_deferred_field_call(
                    project, rule, module, (scope, metadata)
                ):
                    continue
                source = ast.get_source_segment(module.source_code, metadata)
                if source is not None:
                    begin = runtime.source_offset(module.source_code, metadata)
                    regions.append((begin, begin + len(source)))
        return tuple(regions)

    @staticmethod
    def _pure_deferred_field_call(
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        candidate: tuple[p.Infra.RopeScope, ast.Call],
    ) -> bool:
        """Keep builtin factories as values, never evaluate authored callbacks.

        Returns:
            Whether this exact SDK call has one inert deferred-factory argument.

        """
        scope, call = candidate
        if call.args or len(call.keywords) != 1 or rule.call_target is None:
            return False
        keyword = call.keywords[0]
        if keyword.arg != "default_factory" or not isinstance(keyword.value, ast.Name):
            return False
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        builtin = (
            FlextInfraUtilitiesTypesRopeRuntime
            .require_semantic_module(project.get_module("__builtin__"))
            .get_attributes()
            .get(keyword.value.id)
        )
        constraint = rule.arguments.get(rule.call_target)
        if (
            builtin is None
            or constraint is None
            or not runtime.same_name(
                builtin, runtime.resolve_symbol(scope, keyword.value)
            )
        ):
            return False
        if FlextInfraUtilitiesCodemodProject.single_reaching_declarations(
            module, scope, keyword.value.id
        ):
            return False
        if not FlextInfraUtilitiesRopeRuntimeRefactors.semantic_capture(
            project, module, call.func, constraint, name=rule.call_target
        ):
            return False
        callee = ast.unparse(call.func)
        return all(
            FlextInfraUtilitiesCodemodProject.single_reaching_binding(
                module, scope, name, runtime.source_offset(module.source_code, call)
            )
            for name in dict.fromkeys((callee.partition(".")[0], callee))
        )

    @classmethod
    def _plan_model_fields(
        cls,
        sources: Mapping[Path, str],
    ) -> p.Result[tuple[m.Infra.SemanticMigrationEdit, ...]]:
        """Inspect all sources, including direct access emitted by older rules.

        Returns:
            The resulting ``p.Result[tuple[m.Infra.SemanticMigrationEdit, ...]]``.

        """
        return cls._semantic_edits(cls._editable_sources(sources), cls._rewrite_fields)

    @classmethod
    def _rewrite_fields(cls, path: Path, source: str) -> t.Infra.TransformResult:
        tree = ast.parse(source, filename=str(path))
        replacements: list[tuple[int, int, str]] = []
        lines = source.splitlines(keepends=True)
        for function in ast.walk(tree):
            if not isinstance(function, c.Infra.AST_FUNCTION_TYPES):
                continue
            replacements.extend(
                cls._function_field_replacements(path, function, lines),
            )
        if not replacements:
            return source, ()
        cls._require_unshadowed_guard(tree)
        for start, end, replacement in sorted(replacements, reverse=True):
            lines[start:end] = [replacement]
        updated = FlextInfraUtilitiesRopeModulePatch.ensure_from_import(
            "".join(lines),
            module="flext_core",
            name="u",
        )
        return updated, ("narrowed untrusted model-class boundaries",)

    @classmethod
    def _function_field_replacements(
        cls,
        path: Path,
        function: ast.FunctionDef | ast.AsyncFunctionDef,
        lines: Sequence[str],
    ) -> Sequence[tuple[int, int, str]]:
        """Plan the narrowed model-fields boundary of one function body.

        Returns:
            The resulting ``Sequence[tuple[int, int, str]]``.

        Raises:
            ValueError: If a model field guard has no complete source span.

        """
        untrusted = {
            arg.arg
            for arg in (
                *function.args.posonlyargs,
                *function.args.args,
                *function.args.kwonlyargs,
            )
            if isinstance(arg.annotation, ast.Name) and arg.annotation.id == "object"
        }
        replacements: list[tuple[int, int, str]] = []
        for index, statement in enumerate(function.body):
            receiver = cls._field_receiver(statement)
            if receiver not in untrusted or not isinstance(statement, ast.Assign):
                continue
            guard = function.body[index + 1] if index + 1 < len(function.body) else None
            target = statement.targets[0]
            if not isinstance(target, ast.Name):
                continue
            guard = cls._validated_field_boundary(
                path,
                function,
                statement,
                guard,
                target,
            )
            indent = lines[statement.lineno - 1][: statement.col_offset]
            comments = "".join(lines[statement.end_lineno : guard.lineno - 1])
            condition = (
                f"{indent}if (\n"
                f"{indent}    not isinstance({receiver}, type)\n"
                f"{indent}    or not u.model_type({receiver})\n"
                f"{indent}    or not {receiver}.model_fields\n"
                f"{indent}):\n"
            )
            test_end = guard.test.end_lineno
            if test_end is None:
                msg = (
                    f"model field guard has no complete source span in "
                    f"{path}:{statement.lineno}"
                )
                raise ValueError(msg)
            replacements.append((
                statement.lineno - 1,
                test_end,
                comments + condition,
            ))
        return replacements

    @classmethod
    def _validated_field_boundary(
        cls,
        path: Path,
        function: ast.FunctionDef | ast.AsyncFunctionDef,
        statement: ast.Assign,
        guard: ast.stmt | None,
        target: ast.Name,
    ) -> ast.If:
        """Require one complete, guarded, singly used model-fields boundary.

        Returns:
            The validated rejecting guard statement.

        Raises:
            TypeError: If the model field rejection is not an if statement.
            ValueError: If the boundary lacks a rejecting guard, carries
                additional uses, spans invalid source, or rebinds the
                receiver.

        """
        if not cls._rejecting_guard(guard, target.id):
            msg = (
                f"untrusted model_fields access lacks a rejecting "
                f"guard in {path}:{statement.lineno}"
            )
            raise ValueError(msg)
        if not isinstance(guard, ast.If):
            msg = "model field rejection must be an if statement"
            raise TypeError(msg)
        uses = {
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Name) and node.id == target.id
        }
        guarded_uses = {
            node
            for node in ast.walk(guard.test)
            if isinstance(node, ast.Name) and node.id == target.id
        }
        if uses != guarded_uses | {target}:
            msg = f"model_fields local has additional uses in {path}:{statement.lineno}"
            raise ValueError(msg)
        if statement.end_lineno is None or guard.test.end_lineno is None:
            msg = "model field boundary has no complete source span"
            raise ValueError(msg)
        if (
            statement.end_lineno >= guard.lineno
            or guard.body[0].lineno <= guard.test.end_lineno
        ):
            msg = (
                f"model field boundary requires separate indented "
                f"statements in {path}:{statement.lineno}"
            )
            raise ValueError(msg)
        receiver = cls._field_receiver(statement)
        if any(
            receiver in cls.bound_identifiers(node)
            for body in function.body
            for node in ast.walk(body)
        ):
            msg = f"model field receiver is rebound in {path}:{statement.lineno}"
            raise ValueError(msg)
        return guard

    @staticmethod
    def _field_receiver(statement: ast.stmt) -> str | None:
        """Identify a single field assignment without evaluating its receiver.

        Returns:
            The resulting ``str | None``.

        """
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            return None
        value = statement.value
        if isinstance(value, ast.Attribute) and value.attr == "model_fields":
            return value.value.id if isinstance(value.value, ast.Name) else None
        if not isinstance(value, ast.Call) or value.keywords:
            return None
        if not isinstance(value.func, ast.Name) or value.func.id != "getattr":
            return None
        return FlextInfraUtilitiesSemanticCutoverModelFields._getattr_fields_receiver(
            value,
        )

    @staticmethod
    def _getattr_fields_receiver(value: ast.Call) -> str | None:
        """Return the receiver of a ``getattr(x, "model_fields", ...)`` call.

        Returns:
            The resulting ``str | None``.

        """
        match value.args:
            case [ast.Name(id=receiver), ast.Constant(value="model_fields")]:
                return receiver
            case [
                ast.Name(id=receiver),
                ast.Constant(value="model_fields"),
                ast.Constant(),
            ]:
                return receiver
            case [
                ast.Name(id=receiver),
                ast.Constant(value="model_fields"),
                ast.Dict(keys=[]),
            ]:
                return receiver
            case _:
                return None

    @staticmethod
    def _rejecting_guard(statement: ast.stmt | None, target: str) -> bool:
        """Require exactly the original shape error and an unconditional raise.

        Returns:
            The resulting ``bool``.

        """
        if not isinstance(statement, ast.If) or statement.orelse:
            return False
        expected = ast.parse(
            f"not isinstance({target}, dict) or not {target}",
            mode="eval",
        ).body
        return (
            ast.dump(statement.test) == ast.dump(expected)
            and bool(statement.body)
            and isinstance(statement.body[-1], ast.Raise)
        )


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverModelFields"]
