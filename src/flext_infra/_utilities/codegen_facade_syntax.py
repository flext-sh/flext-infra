"""Concrete syntax and declaration checks for generated facades.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import override

from libcst import (
    Arg,
    BaseStatement,
    ClassDef,
    Comma,
    CSTTransformer,
    ImportAlias,
    ImportFrom,
    ImportStar,
    LeftParen,
    MaybeSentinel,
    Module,
    ParenthesizedWhitespace,
    RightParen,
    SimpleStatementLine,
    SimpleWhitespace,
    parse_expression,
    parse_module,
)
from libcst.metadata import MetadataWrapper, PositionProvider

from flext_infra import config, t
from flext_infra._utilities import FlextInfraUtilitiesCodegenNamespace


class FlextInfraUtilitiesCodegenFacadeSyntax:
    """Preserve facade syntax and enforce pure declaration boundaries."""

    @staticmethod
    def _mergeable_import(
        module: Module,
        statement: BaseStatement,
    ) -> t.Pair[str, ImportFrom] | None:
        """Return the module name and node of one absolute member import.

        Returns:
            The imported module spelling and its node, or None for any other
            statement (relative, star and module imports keep their form).

        """
        if not isinstance(statement, SimpleStatementLine) or len(statement.body) != 1:
            return None
        node = statement.body[0]
        if (
            not isinstance(node, ImportFrom)
            or isinstance(node.names, ImportStar)
            or node.relative
            or node.module is None
        ):
            return None
        return module.code_for_node(node.module), node

    @staticmethod
    def _merged_facade_imports(source: str) -> str:
        """Normalize absolute from-imports into one Ruff isort block per module.

        The package-form rewrite leaves one statement per owner bound from the
        same package, sometimes inside a reflowed parenthesized block. Ruff
        isort merges them and orders members by type, so an unmerged
        projection makes ``make fix`` rewrite generated output and breaks the
        generation fixed point. Every absolute member import is rebuilt once
        per module, at its first position, with members in isort order; the
        line budget is applied afterwards by ``_wrap_facade_imports``.

        Returns:
            Source whose absolute from-imports appear once per module.

        """
        module = parse_module(source)
        mergeable = FlextInfraUtilitiesCodegenFacadeSyntax._mergeable_import
        members: t.MutableMappingKV[str, t.MutableMappingKV[str, ImportAlias]] = {}
        for statement in module.body:
            found = mergeable(module, statement)
            if found is None or isinstance(found[1].names, ImportStar):
                continue
            bucket = members.setdefault(found[0], {})
            for item in tuple(found[1].names):
                plain = item.with_changes(comma=MaybeSentinel.DEFAULT)
                bucket.setdefault(module.code_for_node(plain), plain)
        body: list[BaseStatement] = []
        emitted: set[str] = set()
        for statement in module.body:
            found = mergeable(module, statement)
            if found is None:
                body.append(statement)
                continue
            name, node = found
            if name in emitted:
                continue
            emitted.add(name)
            ordered = sorted(
                members[name].values(),
                key=lambda item: (
                    FlextInfraUtilitiesCodegenNamespace.isort_member_key(
                        module.code_for_node(item.name),
                    ),
                    item.asname is not None,
                ),
            )
            names = (
                *tuple(
                    item.with_changes(
                        comma=Comma(whitespace_after=SimpleWhitespace(" "))
                    )
                    for item in ordered[:-1]
                ),
                ordered[-1],
            )
            body.append(
                statement.with_changes(
                    body=(
                        node.with_changes(
                            names=names,
                            lpar=None,
                            rpar=None,
                        ),
                    ),
                ),
            )
        return module.with_changes(body=tuple(body)).code

    @staticmethod
    def _facade_module_declarations(
        tree: ast.Module, facade: ast.ClassDef, pkg_dir: Path
    ) -> None:
        for statement in tree.body:
            if (
                statement is facade
                or isinstance(statement, ast.Import | ast.ImportFrom)
                or (
                    isinstance(statement, ast.Expr)
                    and isinstance(statement.value, ast.Constant)
                    and isinstance(statement.value.value, str)
                )
            ):
                continue
            value = (
                statement.value
                if isinstance(
                    statement,
                    ast.Assign | ast.AnnAssign,
                )
                else None
            )
            targets = (
                statement.targets
                if isinstance(statement, ast.Assign)
                else (statement.target,)
                if isinstance(statement, ast.AnnAssign)
                else ()
            )
            if (
                targets
                and all(isinstance(target, ast.Name) for target in targets)
                and (
                    all(
                        isinstance(target, ast.Name) and target.id == "__all__"
                        for target in targets
                    )
                    or (isinstance(value, ast.Name) and value.id == facade.name)
                )
            ):
                continue
            message = (
                "Facade preserves authored module declaration: "
                f"{pkg_dir}:{statement.lineno}"
            )
            raise ValueError(message)

    @staticmethod
    def _facade_owner_declarations(
        owner: ast.ClassDef,
        facade: ast.ClassDef,
        namespace: ast.ClassDef,
        aliases: set[str],
        pkg_dir: Path,
    ) -> None:
        for statement in owner.body:
            if isinstance(statement, ast.Pass) or (
                statement is namespace and namespace is not facade
            ):
                continue
            if (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
            ):
                continue
            if (
                isinstance(statement, ast.Assign)
                and isinstance(statement.value, ast.Name)
                and statement.value.id in aliases
                and all(isinstance(target, ast.Name) for target in statement.targets)
            ):
                continue
            message = (
                f"Facade preserves authored declaration before generation: "
                f"{pkg_dir}:{owner.name}:{statement.lineno}"
            )
            raise ValueError(message)

    @staticmethod
    def _wrap_facade_imports(source: str) -> str:
        """Keep projected imports inside the configured Ruff line budget.

        Returns:
            Source with long single-line from-imports parenthesized.

        """
        module = parse_module(source)

        class WrapImports(CSTTransformer):
            """Wrap each emitted import in a single concrete-syntax traversal."""

            @override
            def leave_ImportFrom(
                self,
                original_node: ImportFrom,
                updated_node: ImportFrom,
            ) -> ImportFrom:
                """Preserve bindings and wrap only imports exceeding the budget.

                Returns:
                    The original import or its parenthesized equivalent.

                """
                if (
                    isinstance(updated_node.names, ImportStar)
                    or "\n" in module.code_for_node(original_node)
                    or len(module.code_for_node(original_node))
                    <= config.Infra.tooling.tools.ruff.line_length
                ):
                    return updated_node
                return updated_node.with_changes(
                    lpar=LeftParen(
                        whitespace_after=ParenthesizedWhitespace(
                            last_line=SimpleWhitespace("    "),
                        ),
                    ),
                    names=tuple(
                        alias.with_changes(
                            comma=Comma(
                                whitespace_after=ParenthesizedWhitespace(
                                    last_line=SimpleWhitespace(
                                        "    "
                                        if index < len(updated_node.names) - 1
                                        else "",
                                    ),
                                ),
                            ),
                        )
                        for index, alias in enumerate(updated_node.names)
                    ),
                    rpar=RightParen(),
                )

        return module.visit(WrapImports()).code

    @staticmethod
    def _declared_facade_bases(
        owner: ClassDef,
        ordered: t.SequenceOf[str],
    ) -> tuple[Arg, ...]:
        """Build the reordered base arguments for the facade namespace.

        Returns:
            One base argument per ordered name, preserving the source C3 order.

        """
        return tuple(
            (
                owner.bases[-1] if index == len(ordered) - 1 else owner.bases[0]
            ).with_changes(value=parse_expression(name))
            if owner.bases
            else Arg(parse_expression(name))
            for index, name in enumerate(ordered)
        )

    @staticmethod
    def _facade_namespace_cst(
        wrapper: MetadataWrapper,
        namespace: ast.ClassDef,
    ) -> ClassDef:
        """Resolve the unique concrete class span of the projected namespace.

        Returns:
            The concrete namespace class.

        Raises:
            ValueError: If the namespace lacks one exact class span.

        """
        owners = tuple(
            node
            for node, span in wrapper.resolve(PositionProvider).items()
            if isinstance(node, ClassDef)
            and span.start.line == namespace.lineno
            and node.name.value == namespace.name
        )
        if len(owners) != 1:
            message = "Facade namespace has no unique concrete source span"
            raise ValueError(message)
        return owners[0]


__all__: list[str] = ["FlextInfraUtilitiesCodegenFacadeSyntax"]
