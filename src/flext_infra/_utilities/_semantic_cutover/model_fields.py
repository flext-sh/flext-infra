"""Prove native field metadata and narrow untrusted model-class boundaries.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

import libcst as cst
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor

from flext_infra._utilities import (
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
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
    ) -> t.MappingKV[str, str | t.StrSequence]:
        """Constrain ordinary captures before native call admission."""
        if rule.ownership_transfer is not None:
            if len(rule.arguments) != 1 or not all(
                isinstance(value, str) and value.startswith("name=")
                for value in rule.arguments.values()
            ):
                msg = f"{rule.id}: ownership transfer requires one native receiver constraint"
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
        """Prove native model metadata without evaluating authored expressions."""
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
        if invocation is None or constraint is None:
            return False
        if not FlextInfraUtilitiesRopeRuntimeRefactors.semantic_capture(
            project, module, invocation.func, constraint, name=rule.call_target
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
            if isinstance(node, (ast.Name, ast.Attribute))
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

    @classmethod
    def _plan_model_fields(
        cls,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Inspect all sources, including direct access emitted by older rules.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]``.

        """
        return cls._semantic_edits(cls._editable_sources(sources), cls._rewrite_fields)

    @classmethod
    def _rewrite_fields(cls, path: Path, source: str) -> t.Infra.TransformResult:
        tree = ast.parse(source, filename=str(path))
        replacements: list[t.Triple[int, int, str]] = []
        lines = source.splitlines(keepends=True)
        for function in ast.walk(tree):
            if not isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            replacements.extend(
                cls._function_field_replacements(path, function, lines),
            )
        if not replacements:
            return source, ()
        cls._require_unshadowed_guard(tree)
        for start, end, replacement in sorted(replacements, reverse=True):
            lines[start:end] = [replacement]
        context = CodemodContext()
        AddImportsVisitor.add_needed_import(context, "flext_core", "u")
        updated = (
            AddImportsVisitor(context)
            .transform_module(cst.parse_module("".join(lines)))
            .code
        )
        return updated, ("narrowed untrusted model-class boundaries",)

    @classmethod
    def _function_field_replacements(
        cls,
        path: Path,
        function: ast.FunctionDef | ast.AsyncFunctionDef,
        lines: t.SequenceOf[str],
    ) -> t.SequenceOf[t.Triple[int, int, str]]:
        """Plan the narrowed model-fields boundary of one function body.

        Returns:
            The resulting ``t.SequenceOf[t.Triple[int, int, str]]``.

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
        replacements: list[t.Triple[int, int, str]] = []
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
