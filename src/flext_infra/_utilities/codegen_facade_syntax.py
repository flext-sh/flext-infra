"""Concrete syntax preservation for generated facades.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from typing import override

from libcst import (
    Arg,
    Attribute,
    BaseExpression,
    ClassDef,
    Comma,
    CSTNode,
    CSTTransformer,
    CSTVisitor,
    If,
    ImportFrom,
    ImportStar,
    IndentedBlock,
    LeftParen,
    MaybeSentinel,
    Name,
    ParenthesizedWhitespace,
    Pass,
    RemovalSentinel,
    RemoveFromParent,
    RightParen,
    SimpleStatementLine,
    SimpleStatementSuite,
    SimpleWhitespace,
    parse_expression,
    parse_module,
)
from libcst.helpers import get_full_name_for_node
from libcst.metadata import (
    MetadataWrapper,
    PositionProvider,
    QualifiedNameProvider,
    ScopeProvider,
)

from flext_infra import c, config, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesProjectManagedArtifacts,
)


class FlextInfraUtilitiesCodegenFacadeSyntax:
    """Preserve facade syntax while composing declared owners."""

    class WrapImports(CSTTransformer):
        """Wrap emitted imports using the declared module and line budget."""

        def __init__(self, module: t.Infra.CstModule, line_length: int) -> None:
            super().__init__()
            self._module = module
            self._line_length = line_length

        @override
        def leave_ImportFrom(
            self,
            original_node: t.Infra.CstImport,
            updated_node: t.Infra.CstImport,
        ) -> t.Infra.CstImport:
            """Preserve bindings and wrap only imports exceeding the budget.

            Returns:
                The original import or its parenthesized equivalent.

            """
            if (
                isinstance(updated_node.names, ImportStar)
                or "\n" in self._module.code_for_node(original_node)
                or len(self._module.code_for_node(original_node)) <= self._line_length
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

    class DeadTypeCheckingScaffold(CSTTransformer):
        """Remove ``if TYPE_CHECKING:`` blocks whose body is only ``pass``."""

        @override
        def leave_If(
            self,
            original_node: If,
            updated_node: If,
        ) -> If | RemovalSentinel:
            """Drop an empty guard block and keep every other conditional.

            Returns:
                The removal sentinel for an empty guard, else the node.

            """
            del original_node
            body = updated_node.body
            statements = (
                body.body
                if isinstance(body, SimpleStatementSuite | IndentedBlock)
                else ()
            )
            inner = (
                statements[0].body
                if len(statements) == 1
                and isinstance(statements[0], SimpleStatementLine)
                else ()
            )
            if (
                isinstance(updated_node.test, Name)
                and updated_node.test.value == c.Infra.TYPING_GUARD_NAME
                and len(inner) == 1
                and isinstance(inner[0], Pass)
            ):
                return RemoveFromParent()
            return updated_node

    class TypeCheckingGuardScanner(CSTVisitor):
        """Detect a surviving bare or ``typing``-qualified guard test."""

        def __init__(self) -> None:
            """Start unguarded."""
            super().__init__()
            self.guarded = False

        @override
        def on_visit(self, node: CSTNode) -> bool:
            """Flag the first surviving guard test.

            Returns:
                Always ``True`` so descendant nodes stay on the scan path.

            """
            if isinstance(node, If) and self._guard_test(node.test):
                self.guarded = True
            return True

        @staticmethod
        def _guard_test(test: BaseExpression) -> bool:
            return (
                isinstance(test, Name) and test.value == c.Infra.TYPING_GUARD_NAME
            ) or (
                isinstance(test, Attribute)
                and test.attr.value == c.Infra.TYPING_GUARD_NAME
                and isinstance(test.value, Name)
                and test.value.value == c.Infra.TYPING_GUARD_MODULE
            )

    class OrphanTypeCheckingImport(CSTTransformer):
        """Drop the ``TYPE_CHECKING`` import once no guard reads the name."""

        def __init__(self, *, guarded: bool) -> None:
            """Bind whether a surviving guard still reads the name."""
            super().__init__()
            self._guarded = guarded

        @override
        def leave_ImportFrom(
            self,
            original_node: ImportFrom,
            updated_node: ImportFrom,
        ) -> ImportFrom | RemovalSentinel:
            """Strip the guard name from an orphan ``typing`` import.

            Returns:
                The import without the guard name, the removal sentinel, or
                the unchanged import.

            """
            del original_node
            module = updated_node.module
            names = updated_node.names
            if (
                self._guarded
                or not (
                    isinstance(module, Name)
                    and module.value == c.Infra.TYPING_GUARD_MODULE
                )
                or isinstance(names, ImportStar)
            ):
                return updated_node
            kept = tuple(
                alias
                for alias in names
                if not (
                    isinstance(alias.name, Name)
                    and alias.name.value == c.Infra.TYPING_GUARD_NAME
                )
            )
            if len(kept) == len(names):
                return updated_node
            if not kept:
                return RemoveFromParent()
            return updated_node.with_changes(names=kept)

    class OwnPackageUnalias(CSTTransformer):
        """Rename own-package alias references to their imported identity."""

        METADATA_DEPENDENCIES = (QualifiedNameProvider, ScopeProvider)

        def __init__(self, selected: t.MappingKV[t.Pair[str, str], str]) -> None:
            """Bind ``(alias, qualified import)`` to the imported name."""
            super().__init__()
            self._selected = selected

        @override
        def leave_Name(self, original_node: Name, updated_node: Name) -> Name:
            """Rename one reference bound to a selected alias.

            Returns:
                The renamed reference, or the unchanged node.

            Raises:
                ValueError: If the alias is ambiguous or its destination occupied.

            """
            names = tuple(self.get_metadata(QualifiedNameProvider, original_node, ()))
            targets = {
                self._selected[key]
                for name in names
                if (key := (original_node.value, name.name)) in self._selected
            }
            if not targets:
                return updated_node
            if len(targets) != 1 or len(names) != 1:
                msg = f"ambiguous imported alias: {original_node.value}"
                raise ValueError(msg)
            target = next(iter(targets))
            if target == original_node.value:
                return updated_node
            scope = self.get_metadata(ScopeProvider, original_node, None)
            if scope is None:
                msg = f"import alias reference has no scope: {original_node.value}"
                raise ValueError(msg)
            if scope[target]:
                msg = f"import alias destination is occupied: {target}"
                raise ValueError(msg)
            return updated_node.with_changes(value=target)

        @override
        def leave_ImportFrom(
            self, original_node: ImportFrom, updated_node: ImportFrom
        ) -> ImportFrom:
            """Drop the selected aliases from their import statement.

            Returns:
                The import without the selected aliases.

            """
            module = (
                get_full_name_for_node(original_node.module)
                if original_node.module is not None
                else None
            )
            if isinstance(updated_node.names, ImportStar):
                return updated_node
            return updated_node.with_changes(
                names=tuple(
                    alias.with_changes(asname=None)
                    if alias.asname is not None
                    and isinstance(alias.asname.name, Name)
                    and (
                        alias.asname.name.value,
                        f"{module}.{get_full_name_for_node(alias.name)}",
                    )
                    in self._selected
                    else alias
                    for alias in updated_node.names
                )
            )

    @staticmethod
    def unalias_own_package_imports(*, package: str, source: str) -> str:
        """Remove own-package aliases, refusing capture of shadowed bindings.

        Returns:
            Source with references bound to the imported identity renamed.

        """
        selected = {
            (alias.asname, f"{node.module}.{alias.name}"): alias.name
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and (node.module == package or node.module.startswith(f"{package}."))
            for alias in node.names
            if alias.asname is not None
            and alias.asname != alias.name
            and alias.asname not in c.Infra.ALIAS_NAMES
        }
        if not selected:
            return source
        return (
            MetadataWrapper(parse_module(source))
            .visit(FlextInfraUtilitiesCodegenFacadeSyntax.OwnPackageUnalias(selected))
            .code
        )

    @staticmethod
    def strip_type_checking_scaffold(source: str) -> str:
        """Drop empty ``TYPE_CHECKING`` blocks, then their orphan guard import.

        The guard import survives while any guard still reads the name;
        stripping it then would unbind the name, and keeping it after the
        last block is gone leaves a dead import.

        Returns:
            The source without empty guard blocks or an orphan guard import.

        """
        syntax = FlextInfraUtilitiesCodegenFacadeSyntax
        module = parse_module(source).visit(syntax.DeadTypeCheckingScaffold())
        scanner = syntax.TypeCheckingGuardScanner()
        module.visit(scanner)
        return module.visit(
            syntax.OrphanTypeCheckingImport(guarded=scanner.guarded)
        ).code

    @staticmethod
    def _mergeable_import(
        module: t.Infra.CstModule,
        statement: t.Infra.CstStatement,
    ) -> t.Pair[str, t.Infra.CstImport] | None:
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
        members: t.MutableMappingKV[
            str, t.MutableMappingKV[str, t.Infra.CstImportAlias]
        ] = {}
        for statement in module.body:
            found = mergeable(module, statement)
            if found is None or isinstance(found[1].names, ImportStar):
                continue
            bucket = members.setdefault(found[0], {})
            for item in tuple(found[1].names):
                plain = item.with_changes(comma=MaybeSentinel.DEFAULT)
                bucket.setdefault(module.code_for_node(plain), plain)
        body: list[t.Infra.CstStatement] = []
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
    def _wrap_facade_imports(source: str) -> str:
        """Keep projected imports inside the configured Ruff line budget.

        Returns:
            Source with long single-line from-imports parenthesized.

        """
        module = parse_module(source)
        return module.visit(
            FlextInfraUtilitiesCodegenFacadeSyntax.WrapImports(
                module,
                FlextInfraUtilitiesProjectManagedArtifacts.native_tool_setting(
                    config.Infra.tooling, "ruff", "line-length", int
                ),
            ),
        ).code

    @staticmethod
    def _declared_facade_bases(
        owner: t.Infra.CstClass,
        ordered: t.SequenceOf[str],
    ) -> tuple[t.Infra.CstArgument, ...]:
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
        wrapper: t.Infra.CstMetadata,
        namespace: t.Infra.PythonClassNode,
    ) -> t.Infra.CstClass:
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
