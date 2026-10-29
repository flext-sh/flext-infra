"""Concrete syntax preservation for generated facades.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, MutableMapping, Sequence
from typing import override

from libcst import (
    Arg,
    ClassDef,
    CSTTransformer,
    ImportFrom,
    ImportStar,
    Name,
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

    @classmethod
    def _is_type_checking_test(cls, test: ast.expr) -> bool:
        """Return whether one condition tests the typing guard name.

        Returns:
            Whether the test is the bare or ``typing``-qualified guard name.

        """
        if isinstance(test, ast.Name):
            return test.id == c.Infra.TYPING_GUARD_NAME
        return (
            isinstance(test, ast.Attribute)
            and test.attr == c.Infra.TYPING_GUARD_NAME
            and isinstance(test.value, ast.Name)
            and test.value.id == c.Infra.TYPING_GUARD_MODULE
        )

    @classmethod
    def _drop_empty_type_checking_blocks(cls, source: str) -> str:
        """Delete every empty guard block's complete source lines.

        Returns:
            The source without ``if TYPE_CHECKING: pass`` blocks.

        """
        spans = {
            (node.lineno, node.end_lineno or node.lineno)
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.If)
            and cls._is_type_checking_test(node.test)
            and len(node.body) == 1
            and isinstance(node.body[0], ast.Pass)
        }
        lines = source.splitlines(keepends=True)
        for start, end in sorted(spans, reverse=True):
            del lines[start - 1 : end]
        return "".join(lines)

    @classmethod
    def _drop_orphan_type_checking_import(cls, source: str, tree: ast.Module) -> str:
        """Strip the guard name from its import when no guard survives.

        Returns:
            The source without the orphan guard import alias.

        """
        lines = source.splitlines(keepends=True)
        plans: list[tuple[int, int, str | None]] = [
            cls._import_replacement_plan(
                lines,
                node,
                [
                    alias
                    for alias in node.names
                    if alias.name != c.Infra.TYPING_GUARD_NAME
                ],
            )
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and cls._is_orphan_guard_import(node)
        ]
        for start, end, replacement in sorted(plans, reverse=True):
            lines[start - 1 : end] = [replacement] if replacement is not None else []
        return "".join(lines)

    @staticmethod
    def _is_orphan_guard_import(node: ast.AST) -> bool:
        """Return whether one node imports the guard name from typing.

        Returns:
            Whether the node is an absolute typing import binding the guard.

        """
        return (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module == c.Infra.TYPING_GUARD_MODULE
            and any(alias.name == c.Infra.TYPING_GUARD_NAME for alias in node.names)
        )

    @classmethod
    def _import_replacement_plan(
        cls,
        lines: Sequence[str],
        node: ast.ImportFrom,
        kept: Sequence[ast.alias],
    ) -> tuple[int, int, str | None]:
        """Plan one import statement's replacement after alias removal.

        Returns:
            The line range and its replacement, or ``None`` text to delete.

        """
        end = node.end_lineno or node.lineno
        if not kept:
            return (node.lineno, end, None)
        indent = lines[node.lineno - 1][: node.col_offset]
        members = ", ".join(ast.unparse(alias) for alias in kept)
        return (node.lineno, end, f"{indent}from {node.module} import {members}\n")

    class OwnPackageUnalias(CSTTransformer):
        """Rename own-package alias references to their imported identity."""

        METADATA_DEPENDENCIES = (QualifiedNameProvider, ScopeProvider)

        def __init__(self, selected: Mapping[tuple[str, str], str]) -> None:
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

    @classmethod
    def strip_type_checking_scaffold(cls, source: str) -> str:
        """Drop empty ``TYPE_CHECKING`` blocks, then their orphan guard import.

        The guard import survives while any guard still reads the name;
        stripping it then would unbind the name, and keeping it after the
        last block is gone leaves a dead import.

        Returns:
            The source without empty guard blocks or an orphan guard import.

        """
        stripped = cls._drop_empty_type_checking_blocks(source)
        tree = ast.parse(stripped)
        guarded = any(
            isinstance(node, ast.If) and cls._is_type_checking_test(node.test)
            for node in ast.walk(tree)
        )
        if guarded:
            return stripped
        return cls._drop_orphan_type_checking_import(stripped, tree)

    @staticmethod
    def _mergeable_import(statement: ast.stmt) -> str | None:
        """Return the module name of one absolute member import statement.

        Returns:
            The imported module spelling, or None for any other statement
            (relative, star and module imports keep their form).

        """
        if (
            not isinstance(statement, ast.ImportFrom)
            or statement.level
            or statement.module is None
            or any(alias.name == "*" for alias in statement.names)
        ):
            return None
        return statement.module

    @classmethod
    def _merged_facade_imports(cls, source: str) -> str:
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
        tree = ast.parse(source)
        members: MutableMapping[str, MutableMapping[str, str]] = {}
        for statement in tree.body:
            module_name = cls._mergeable_import(statement)
            if not isinstance(statement, ast.ImportFrom) or module_name is None:
                continue
            bucket = members.setdefault(module_name, {})
            for alias in statement.names:
                bucket.setdefault(ast.unparse(alias), alias.name)
        plans: list[tuple[int, int, str | None]] = []
        emitted: set[str] = set()
        for statement in tree.body:
            module_name = cls._mergeable_import(statement)
            if module_name is None:
                continue
            if module_name in emitted:
                plans.append((
                    statement.lineno,
                    statement.end_lineno or statement.lineno,
                    None,
                ))
                continue
            emitted.add(module_name)
            ordered = sorted(
                members[module_name].items(),
                key=lambda item: (
                    FlextInfraUtilitiesCodegenNamespace.isort_member_key(item[1]),
                    " as " in item[0],
                ),
            )
            rendered = ", ".join(alias for alias, _name in ordered)
            plans.append((
                statement.lineno,
                statement.end_lineno or statement.lineno,
                f"from {module_name} import {rendered}\n",
            ))
        lines = source.splitlines(keepends=True)
        for start, end, replacement in sorted(plans, reverse=True):
            lines[start - 1 : end] = [replacement] if replacement is not None else []
        return "".join(lines)

    @classmethod
    def _wrap_facade_imports(cls, source: str) -> str:
        """Keep projected imports inside the configured Ruff line budget.

        Returns:
            Source with long single-line from-imports parenthesized.

        """
        line_length = FlextInfraUtilitiesProjectManagedArtifacts.native_tool_setting(
            config.Infra.tooling,
            "ruff",
            "line-length",
            int,
        )
        plans: list[tuple[int, int, str]] = []
        for statement in ast.parse(source).body:
            if not isinstance(statement, ast.ImportFrom):
                continue
            prefix = cls._import_prefix(statement)
            members = [ast.unparse(alias) for alias in statement.names]
            if (
                statement.end_lineno != statement.lineno
                or "*" in members
                or len(f"{prefix} {', '.join(members)}") <= line_length
            ):
                continue
            wrapped = (
                f"{prefix} (\n"
                + "".join(f"    {member},\n" for member in members)
                + ")"
            )
            plans.append((
                statement.lineno,
                statement.end_lineno or statement.lineno,
                wrapped,
            ))
        lines = source.splitlines(keepends=True)
        for start, end, replacement in sorted(plans, reverse=True):
            lines[start - 1 : end] = [f"{replacement}\n"]
        return "".join(lines)

    @staticmethod
    def _import_prefix(statement: ast.ImportFrom) -> str:
        """Render one import statement's ``from ... import`` header.

        Returns:
            The header text ending in the ``import`` keyword.

        """
        module = f"{'.' * statement.level}{statement.module or ''}"
        return f"from {module} import"

    @staticmethod
    def _declared_facade_bases(
        owner: t.Infra.CstClass,
        ordered: Sequence[str],
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
