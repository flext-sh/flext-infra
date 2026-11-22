"""LibCST codemod retargeting of authenticated imported names.

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
    QualifiedNameProvider,
    QualifiedNameSource,
    ScopeProvider,
)

from flext_infra import t
from flext_infra._utilities import FlextInfraUtilitiesQualifiedNames

if TYPE_CHECKING:
    from collections.abc import Callable


class FlextInfraUtilitiesImportedNames:
    """Rewire imported names through LibCST's native import management.

    Only this owner depends on ``libcst.codemod``; the qualified-name metadata
    helpers stay free of it, so their callers never load the codemod package.
    """

    @classmethod
    def retarget_imported_names(
        cls,
        source: str,
        owner: str,
        paths: tuple[str, str],
        *,
        member_target: Callable[[str], tuple[str, str] | None] | None = None,
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
            identity: tuple[str, str, str],
            member_target: Callable[[str], tuple[str, str] | None] | None,
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
            target: tuple[str, str],
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


__all__: list[str] = ["FlextInfraUtilitiesImportedNames"]
