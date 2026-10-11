"""Binding-aware concrete-syntax rewrites for private imports.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import TYPE_CHECKING, override

import libcst as cst
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.metadata import MetadataWrapper, ParentNodeProvider, QualifiedNameProvider

from flext_infra._utilities import FlextInfraUtilitiesQualifiedNames

if TYPE_CHECKING:
    from flext_infra import m, t


class FlextInfraUtilitiesSemanticCutoverPrivateImportCst:
    """Preserve source layout while moving consumers to public facades.

    Same-package absolute private imports are legal (imports are always
    absolute); only cross-owner private imports reach this rewrite.
    """

    class _DeclaredExports(cst.CSTTransformer):
        """Relocate imports without renaming their consumer-side bindings."""

        def __init__(self, exports: t.MappingKV[str, t.Pair[str, str]]) -> None:
            self.exports = exports

        @override
        def leave_ImportFrom(
            self,
            original_node: cst.ImportFrom,
            updated_node: cst.ImportFrom,
        ) -> cst.BaseSmallStatement | cst.FlattenSentinel[cst.BaseSmallStatement]:

            if original_node.relative or isinstance(
                updated_node.names,
                cst.ImportStar,
            ):
                return updated_node
            dotted_name = FlextInfraUtilitiesQualifiedNames.dotted_name
            module = dotted_name(original_node.module)
            if not any(
                f"{module}.{dotted_name(item.name)}" in self.exports
                for item in updated_node.names
            ):
                return updated_node
            statements: list[cst.BaseSmallStatement] = []
            for imported in updated_node.names:
                name = dotted_name(imported.name)
                if name is None:
                    msg = "declared export import requires a static symbol name"
                    raise ValueError(msg)
                destination = self.exports.get(f"{module}.{name}")
                replacement = imported.with_changes(comma=cst.MaybeSentinel.DEFAULT)
                destination_module = updated_node.module
                if destination is not None:
                    public_module, public_name = destination
                    asname = imported.asname
                    if asname is None and public_name != name:
                        asname = cst.AsName(cst.Name(name))
                    replacement = replacement.with_changes(
                        name=cst.Name(public_name),
                        asname=asname,
                    )
                    destination_module = cst.parse_expression(public_module)
                statements.append(
                    updated_node.with_changes(
                        module=destination_module,
                        names=(replacement,),
                        lpar=None,
                        rpar=None,
                    ),
                )
            return cst.FlattenSentinel(statements)

    @classmethod
    def relocate_declared_exports(
        cls,
        source: str,
        exports: t.MappingKV[str, t.Pair[str, str]],
    ) -> str:
        """Keep lexical scopes and ``as`` aliases while selecting public owners.

        Returns:
            The resulting ``str``.

        """
        return cst.parse_module(source).visit(cls._DeclaredExports(exports)).code

    class _PrivateImportTransformer(cst.CSTTransformer):
        METADATA_DEPENDENCIES = (ParentNodeProvider, QualifiedNameProvider)

        def __init__(self, plan: m.Infra.PrivateImportRewritePlan) -> None:
            self.plan = plan

        @override
        def leave_Name(
            self,
            original_node: cst.Name,
            updated_node: cst.Name,
        ) -> cst.BaseExpression:
            """Replace only names bound to one authenticated private identity.

            Returns:
                The resulting ``cst.BaseExpression``.

            Raises:
                ValueError: If ambiguous private import binding.

            """
            targets = {
                replacement
                for qualified_name in self.get_metadata(
                    QualifiedNameProvider,
                    original_node,
                    (),
                )
                if (replacement := self.plan.replacements.get(qualified_name.name))
                is not None
            }
            if not targets:
                return updated_node
            if len(targets) != 1:
                msg = (
                    f"ambiguous private import binding {original_node.value}: "
                    f"{sorted(targets)}"
                )
                raise ValueError(msg)
            parent = self.get_metadata(ParentNodeProvider, original_node)
            if FlextInfraUtilitiesQualifiedNames.rebinds_name_in_place(
                parent,
                original_node,
            ):
                return updated_node
            target = targets.pop()
            # A consumer that binds the private symbol under the very alias its
            # public facade already publishes (`c`, `t`, `p`, `m`, `u`) spells
            # the final form before the cutover runs: `m.Metadata` is already
            # the target path. Rewriting the base there appends the nested
            # segment a second time and yields `m.Metadata.Metadata`.
            if (
                isinstance(parent, cst.Attribute)
                and parent.value is original_node
                and target.startswith(f"{original_node.value}.")
                and target.endswith(f".{parent.attr.value}")
            ):
                return updated_node
            return cst.parse_expression(target)

        @override
        def leave_ImportFrom(
            self,
            original_node: cst.ImportFrom,
            updated_node: cst.ImportFrom,
        ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
            """Remove cross-owner private bindings replaced by public facades.

            Returns:
                The resulting ``cst.BaseSmallStatement | cst.RemovalSentinel``.

            """
            module = FlextInfraUtilitiesQualifiedNames.dotted_name(
                original_node.module,
            )
            module_name = module or ""
            removed = self.plan.removals.get(
                module_name,
                frozenset(),
            ) | self.plan.obsolete_imports.get(module_name, frozenset())
            canonical = {
                alias
                for alias, package in self.plan.public_imports.items()
                if package == module_name
            }
            if isinstance(updated_node.names, cst.ImportStar) or (
                not removed and not canonical
            ):
                return updated_node
            retained = [
                imported
                for imported in updated_node.names
                if (
                    name := FlextInfraUtilitiesQualifiedNames.dotted_name(
                        imported.name,
                    )
                )
                not in removed
                and not (name in canonical and imported.asname is None)
            ]
            if not retained:
                return cst.RemoveFromParent()
            return updated_node.with_changes(
                names=FlextInfraUtilitiesQualifiedNames.normalized_import_aliases(
                    retained,
                    parenthesized=bool(updated_node.lpar),
                ),
            )

    class _TypeCheckingImports(cst.CSTTransformer):
        """Insert one canonical group for facades used only by annotations."""

        def __init__(self, public_imports: t.StrMapping) -> None:
            self.public_imports = public_imports
            self.inserted = False

        @override
        def leave_If(self, original_node: cst.If, updated_node: cst.If) -> cst.If:
            """Populate the first explicit ``TYPE_CHECKING`` block.

            Returns:
                The resulting ``cst.If``.

            Raises:
                TypeError: If TYPE_CHECKING boundary must use an indented block.

            """
            if (
                self.inserted
                or not isinstance(original_node.test, cst.Name)
                or original_node.test.value != "TYPE_CHECKING"
            ):
                return updated_node
            if not isinstance(updated_node.body, cst.IndentedBlock):
                msg = "TYPE_CHECKING boundary must use an indented block"
                raise TypeError(msg)
            grouped: MutableMapping[str, list[str]] = {}
            for alias, package in sorted(self.public_imports.items()):
                grouped.setdefault(package, []).append(alias)
            imports = tuple(
                cst.parse_statement(f"from {package} import {', '.join(aliases)}\n")
                for package, aliases in sorted(grouped.items())
            )
            self.inserted = True
            return updated_node.with_changes(
                body=updated_node.body.with_changes(
                    body=imports + tuple(updated_node.body.body),
                ),
            )

    class _EmptyTypeChecking(cst.CSTTransformer):
        """Prune exhausted annotation guards without discarding their comments."""

        METADATA_DEPENDENCIES = (QualifiedNameProvider,)

        def __init__(self) -> None:
            self.removed = False
            self.type_guards: set[cst.If] = set()

        @override
        def leave_If(self, original_node: cst.If, updated_node: cst.If) -> cst.If:
            if any(
                name.name == "typing.TYPE_CHECKING"
                for name in self.get_metadata(
                    QualifiedNameProvider, original_node.test, set()
                )
            ):
                self.type_guards.add(updated_node)
            return updated_node

        def _prune(
            self,
            statements: t.SequenceOf[cst.BaseStatement],
        ) -> t.Pair[t.VariadicTuple[cst.BaseStatement], t.VariadicTuple[cst.EmptyLine]]:
            """Return retained statements and any trailing preserved comments.

            Returns:
                The retained suite and its pending comment lines.

            Raises:
                TypeError: If a statement cannot carry preserved leading lines.

            """
            retained: list[cst.BaseStatement] = []
            pending: list[cst.EmptyLine] = []
            for statement in statements:
                if (
                    isinstance(statement, cst.If)
                    and statement in self.type_guards
                    and statement.orelse is None
                    and isinstance(statement.body, cst.IndentedBlock)
                    and all(
                        isinstance(line, cst.SimpleStatementLine)
                        and all(isinstance(item, cst.Pass) for item in line.body)
                        for line in statement.body.body
                    )
                ):
                    self.removed = True
                    pending.extend(statement.leading_lines)
                    header = statement.body.header
                    if header.comment is not None:
                        pending.append(cst.EmptyLine(comment=header.comment))
                    for line in statement.body.body:
                        if isinstance(line, cst.SimpleStatementLine):
                            pending.extend(line.leading_lines)
                            if line.trailing_whitespace.comment is not None:
                                pending.append(
                                    cst.EmptyLine(
                                        comment=line.trailing_whitespace.comment
                                    )
                                )
                    pending.extend(statement.body.footer)
                    continue
                if pending:
                    if not isinstance(
                        statement, (cst.SimpleStatementLine, cst.BaseCompoundStatement)
                    ):
                        msg = "statement cannot preserve exhausted guard comments"
                        raise TypeError(msg)
                    statement = statement.with_changes(
                        leading_lines=tuple(pending) + tuple(statement.leading_lines),
                    )
                    pending.clear()
                retained.append(statement)
            return tuple(retained), tuple(pending)

        @override
        def leave_Module(
            self, original_node: cst.Module, updated_node: cst.Module
        ) -> cst.Module:
            body, footer = self._prune(updated_node.body)
            return updated_node.with_changes(
                body=body, footer=footer + updated_node.footer
            )

        @override
        def leave_IndentedBlock(
            self, original_node: cst.IndentedBlock, updated_node: cst.IndentedBlock
        ) -> cst.IndentedBlock:
            body, footer = self._prune(updated_node.body)
            return updated_node.with_changes(
                body=body, footer=footer + updated_node.footer
            )

    @classmethod
    def _rewrite_private_import_source(
        cls,
        source: str,
        plan: m.Infra.PrivateImportRewritePlan,
        *,
        runtime_public_imports: frozenset[str],
    ) -> str:
        """Return a binding-proven rewrite with required public imports.

        Returns:
            A binding-proven rewrite with required public imports.

        Raises:
            ValueError: If type-only facade migration has no TYPE_CHECKING boundary; or
                if ambiguous private import binding.

        """
        public_imports = plan.public_imports
        transformer = cls._PrivateImportTransformer(plan)
        rewritten = MetadataWrapper(cst.parse_module(source)).visit(transformer)
        context = CodemodContext()
        for facade_alias in sorted(runtime_public_imports):
            package = public_imports[facade_alias]
            AddImportsVisitor.add_needed_import(context, package, facade_alias)
        rewritten = AddImportsVisitor(context).transform_module(rewritten)
        type_only_imports = {
            alias: package
            for alias, package in public_imports.items()
            if alias not in runtime_public_imports
        }
        if type_only_imports:
            type_imports = cls._TypeCheckingImports(type_only_imports)
            rewritten = rewritten.visit(type_imports)
            if not type_imports.inserted:
                msg = "type-only facade migration has no TYPE_CHECKING boundary"
                raise ValueError(msg)
        cleanup = cls._EmptyTypeChecking()
        rewritten = MetadataWrapper(rewritten).visit(cleanup)
        if cleanup.removed:
            RemoveImportsVisitor.remove_unused_import(
                context, "typing", "TYPE_CHECKING"
            )
            rewritten = RemoveImportsVisitor(context).transform_module(rewritten)
        return rewritten.code


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverPrivateImportCst"]
