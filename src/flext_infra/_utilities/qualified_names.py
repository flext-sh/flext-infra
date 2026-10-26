"""LibCST qualified-name metadata utilities.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import libcst as cst
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.metadata import (
    ImportAssignment,
    MetadataWrapper,
    ParentNodeProvider,
    QualifiedName,
    QualifiedNameProvider,
    QualifiedNameSource,
    ScopeProvider,
)

from flext_infra import c, t

if TYPE_CHECKING:
    from collections.abc import Callable, Container

    from flext_infra import p


class FlextInfraUtilitiesQualifiedNames:
    """Resolve lazy LibCST qualified-name metadata through its public visitor API."""

    @classmethod
    def retarget_imported_names(
        cls,
        source: str,
        owner: str,
        paths: t.Pair[str, str],
        *,
        member_target: Callable[[str], t.Pair[str, str] | None] | None = None,
    ) -> str:
        """Rewire proven imported names to an authenticated public member.

        Returns:
            Source with native import management and no lexical capture.

        """
        old, new = paths
        wrapper = MetadataWrapper(cst.parse_module(source))
        context = CodemodContext(wrapper=wrapper)
        rewrite = cls.ImportedNameRewrite(context, (owner, old, new), member_target)
        updated = wrapper.visit(rewrite)
        if updated.deep_equals(wrapper.module):
            return source
        updated = rewrite.apply_guarded_imports(updated)
        updated = AddImportsVisitor(context).transform_module(updated)
        return RemoveImportsVisitor(context).transform_module(updated).code

    class ImportedNameRewrite(cst.CSTTransformer):
        """Retarget authenticated imports while preserving lexical bindings."""

        METADATA_DEPENDENCIES = (
            QualifiedNameProvider,
            ScopeProvider,
            ParentNodeProvider,
        )

        def __init__(
            self,
            context: CodemodContext,
            identity: t.Triple[str, str, str],
            member_target: Callable[[str], t.Pair[str, str] | None] | None,
        ) -> None:
            super().__init__()
            self.context = context
            self.owner, old, self.new = identity
            self.identity = f"{self.owner}.{old}"
            self.member_target = member_target
            self.guards: dict[t.Infra.Cst.If, t.Infra.Cst.If] = {}
            self.guarded_imports: dict[t.Infra.Cst.If, CodemodContext] = {}

        @override
        def leave_If(
            self, original_node: t.Infra.Cst.If, updated_node: t.Infra.Cst.If
        ) -> t.Infra.Cst.If:
            self.guards[original_node] = updated_node
            return updated_node

        def apply_guarded_imports(
            self, module: t.Infra.Cst.Module
        ) -> t.Infra.Cst.Module:
            """Use native import insertion within each original typing guard.

            Returns:
                The module with typing-only imports at their original boundary.

            """
            for guard, context in self.guarded_imports.items():
                updated = self.guards[guard]
                suite = updated.body
                if isinstance(suite, cst.SimpleStatementSuite):
                    statements = (cst.SimpleStatementLine(body=suite.body),)
                else:
                    statements = tuple(
                        statement
                        if isinstance(statement, cst.BaseCompoundStatement)
                        else cst.ensure_type(statement, cst.SimpleStatementLine)
                        for statement in cst.ensure_type(suite, cst.IndentedBlock).body
                    )
                body = AddImportsVisitor(context).transform_module(
                    cst.Module(body=statements)
                )
                module = cst.ensure_type(
                    module.deep_replace(
                        updated,
                        updated.with_changes(
                            body=(
                                updated.body.with_changes(body=body.body)
                                if isinstance(updated.body, cst.IndentedBlock)
                                else cst.IndentedBlock(body=body.body)
                            )
                        ),
                    ),
                    cst.Module,
                )
            return module

        def import_context(
            self, node: t.Infra.Cst.Name | t.Infra.Cst.Attribute
        ) -> CodemodContext:
            """Retain the original import's native lexical typing boundary.

            Returns:
                The native insertion context for the original binding.

            Raises:
                ValueError: If the imported reference has no lexical scope.

            """
            root = FlextInfraUtilitiesQualifiedNames.lexical_root(node)
            scope = self.get_metadata(ScopeProvider, node, None)
            if scope is None:
                msg = "imported reference has no lexical scope"
                raise ValueError(msg)
            if not isinstance(root, cst.Name):
                return self.context
            for assignment in scope[root.value]:
                if not isinstance(assignment, ImportAssignment):
                    continue
                parent = assignment.node
                while parent is not None:
                    if isinstance(parent, cst.If) and any(
                        name.name == "typing.TYPE_CHECKING"
                        for name in self.get_metadata(
                            QualifiedNameProvider, parent.test, ()
                        )
                    ):
                        return self.guarded_imports.setdefault(parent, CodemodContext())
                    parent = self.get_metadata(ParentNodeProvider, parent, None)
            return self.context

        @override
        def leave_Name(
            self,
            original_node: t.Infra.Cst.Name,
            updated_node: t.Infra.Cst.Name,
        ) -> t.Infra.Cst.BaseExpression:
            if self.member_target is not None:
                return updated_node
            return self.retarget(original_node, updated_node, (self.owner, self.new))

        @override
        def leave_Attribute(
            self,
            original_node: t.Infra.Cst.Attribute,
            updated_node: t.Infra.Cst.Attribute,
        ) -> t.Infra.Cst.BaseExpression:
            if self.member_target is None:
                return updated_node
            names = tuple(self.get_metadata(QualifiedNameProvider, original_node, ()))
            imported = tuple(
                name
                for name in names
                if name.source is QualifiedNameSource.IMPORT
                and name.name.startswith(f"{self.identity}.")
            )
            if not imported:
                return updated_node
            if len(names) != 1:
                msg = "ambiguous imported member reference"
                raise ValueError(msg)
            target = self.member_target(imported[0].name)
            if target is None:
                return updated_node
            return self.retarget(original_node, updated_node, target)

        def retarget(
            self,
            original_node: t.Infra.Cst.Name | t.Infra.Cst.Attribute,
            updated_node: t.Infra.Cst.BaseExpression,
            target: t.Pair[str, str],
        ) -> t.Infra.Cst.BaseExpression:
            names = tuple(self.get_metadata(QualifiedNameProvider, original_node, ()))
            if self.member_target is None and not any(
                name.source is QualifiedNameSource.IMPORT and name.name == self.identity
                for name in names
            ):
                return updated_node
            if len(names) != 1:
                msg = "ambiguous imported reference"
                raise ValueError(msg)
            scope = self.get_metadata(ScopeProvider, original_node, None)
            if scope is None:
                msg = "imported reference has no lexical scope"
                raise ValueError(msg)
            target_module, expression = target
            target_receiver = expression.split(".")[0]
            for assignment in scope[target_receiver]:
                qualified = assignment.get_qualified_names_for(target_receiver)
                if not qualified or any(
                    name.source
                    is not (
                        QualifiedNameSource.IMPORT
                        if target_module
                        else QualifiedNameSource.LOCAL
                    )
                    or name.name
                    != (
                        f"{target_module}.{target_receiver}"
                        if target_module
                        else target_receiver
                    )
                    for name in qualified
                ):
                    msg = f"public import receiver is shadowed: {target_receiver}"
                    raise ValueError(msg)
            RemoveImportsVisitor.remove_unused_import_by_node(
                self.context, original_node
            )
            if target_module:
                AddImportsVisitor.add_needed_import(
                    self.import_context(original_node), target_module, target_receiver
                )
            return cst.parse_expression(expression)

    @staticmethod
    def lexical_root(node: t.Infra.Cst.CSTNode) -> t.Infra.Cst.CSTNode:
        """Return the lexical receiver underlying a dotted attribute expression.

        Returns:
            The leftmost receiver node.

        """
        while isinstance(node, c.Infra.Cst.Attribute):
            node = node.value
        return node

    @staticmethod
    def prove_import_root(
        names: t.VariadicTuple[QualifiedName],
        roots: t.VariadicTuple[QualifiedName],
    ) -> frozenset[QualifiedName]:
        """Require imported attribute identities to agree with lexical root bindings.

        Returns:
            Identities compatible with the lexical root, excluding shadowed imports.

        Raises:
            ValueError: If an imported identity has unresolved or competing roots.

        """
        proven: set[QualifiedName] = set()
        for name in names:
            if name.source is not QualifiedNameSource.IMPORT:
                proven.add(name)
                continue
            if not roots:
                msg = "unresolved qualified alias lexical root"
                raise ValueError(msg)
            compatible = [
                root
                for root in roots
                if root.source is QualifiedNameSource.IMPORT
                and (name.name == root.name or name.name.startswith(f"{root.name}."))
            ]
            if not compatible:
                continue
            if len(compatible) != len(roots):
                msg = "ambiguous qualified alias lexical root"
                raise ValueError(msg)
            proven.add(name)
        return frozenset(proven)

    @staticmethod
    def dotted_name(node: t.Infra.Cst.BaseExpression | None) -> str | None:
        """Return a static dotted name, or ``None`` for a dynamic expression.

        Returns:
            A static dotted name, or ``None`` for a dynamic expression.

        """
        if isinstance(node, c.Infra.Cst.Name):
            return node.value
        if isinstance(node, c.Infra.Cst.Attribute):
            parent = FlextInfraUtilitiesQualifiedNames.dotted_name(node.value)
            return f"{parent}.{node.attr.value}" if parent else None
        return None

    @staticmethod
    def without_exports(
        value: t.Infra.Cst.BaseExpression,
        names: Container[str],
    ) -> t.Infra.Cst.BaseExpression:
        """Drop ``names`` from a literal ``__all__`` list or tuple expression.

        Returns:
            The resulting ``cst.BaseExpression``.

        """
        if not isinstance(value, c.Infra.Cst.List | c.Infra.Cst.Tuple):
            return value
        return value.with_changes(
            elements=tuple(
                element
                for element in value.elements
                if not isinstance(element.value, c.Infra.Cst.SimpleString)
                or not isinstance(element.value.evaluated_value, str)
                or element.value.evaluated_value not in names
            ),
        )

    @staticmethod
    def filter_exports[N: (t.Infra.Cst.Assign, t.Infra.Cst.AnnAssign)](
        node: N,
        names: Container[str],
    ) -> N:
        """Drop ``names`` from an ``__all__`` assignment; other assignments pass.

        Returns:
            The resulting ``N``.

        """
        targets = (
            tuple(target.target for target in node.targets)
            if isinstance(node, c.Infra.Cst.Assign)
            else (node.target,)
        )
        if (
            len(targets) != 1
            or not isinstance(targets[0], c.Infra.Cst.Name)
            or targets[0].value != "__all__"
            or node.value is None
        ):
            return node
        return node.with_changes(
            value=FlextInfraUtilitiesQualifiedNames.without_exports(node.value, names),
        )

    @staticmethod
    def normalized_import_aliases(
        aliases: t.SequenceOf[t.Infra.Cst.ImportAlias],
        *,
        parenthesized: bool,
    ) -> t.VariadicTuple[t.Infra.Cst.ImportAlias]:
        """Repair separators after import aliases were dropped or rewritten.

        Returns:
            The resulting ``t.VariadicTuple[cst.ImportAlias]``.

        """
        last_index = len(aliases) - 1
        return tuple(
            alias.with_changes(comma=cst.MaybeSentinel.DEFAULT)
            if index == last_index and not parenthesized
            else alias.with_changes(
                comma=cst.Comma(whitespace_after=cst.SimpleWhitespace(" ")),
            )
            if index < last_index and not isinstance(alias.comma, c.Infra.Cst.Comma)
            else alias
            for index, alias in enumerate(aliases)
        )

    @staticmethod
    def rebinds_name_in_place(
        parent: p.AttributeProbe, node: t.Infra.Cst.CSTNode
    ) -> bool:
        """Return whether ``parent`` spells ``node`` as a binding, not a reference.

        An import alias, an attribute's own ``attr``, and a keyword argument's
         name are written by the surrounding syntax, so a rename must leave them
         exactly as they are.

        Returns:
            Whether ``parent`` spells ``node`` as a binding, not a reference.

        """
        if isinstance(parent, c.Infra.Cst.ImportAlias):
            return True
        if isinstance(parent, c.Infra.Cst.Attribute) and parent.attr is node:
            return True
        return isinstance(parent, c.Infra.Cst.Arg) and parent.keyword is node

    @classmethod
    def qualified_name_residue(
        cls,
        source: str,
        candidates: Container[str],
    ) -> frozenset[str]:
        """Return candidate qualified names referenced by Python source.

        Returns:
            Candidate qualified names referenced by Python source.

        """

        class _ResidueCollector(cst.CSTVisitor):
            METADATA_DEPENDENCIES = (QualifiedNameProvider,)

            def __init__(self, candidates: Container[str]) -> None:
                self.candidates = candidates
                self.residue: set[str] = set()

            @override
            def on_visit(self, node: t.Infra.Cst.CSTNode) -> bool:
                names = tuple(self.get_metadata(QualifiedNameProvider, node, ()))
                if isinstance(node, c.Infra.Cst.Attribute) and any(
                    name.name in self.candidates for name in names
                ):
                    names = tuple(
                        cls.prove_import_root(
                            names,
                            tuple(
                                self.get_metadata(
                                    QualifiedNameProvider,
                                    cls.lexical_root(node),
                                    (),
                                ),
                            ),
                        ),
                    )
                self.residue.update(
                    qualified_name.name
                    for qualified_name in names
                    if qualified_name.name in self.candidates
                )
                return True

        collector = _ResidueCollector(candidates)
        MetadataWrapper(cst.parse_module(source)).visit(collector)
        return frozenset(collector.residue)


__all__: list[str] = ["FlextInfraUtilitiesQualifiedNames"]
