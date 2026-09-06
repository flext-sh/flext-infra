"""Binding-aware concrete-syntax rewrites for private imports."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import libcst as cst
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor
from libcst.metadata import MetadataWrapper, ParentNodeProvider, QualifiedNameProvider

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraUtilitiesPrivateImportCst:
    """Preserve source layout while moving consumers to public facades."""

    class _Transformer(cst.CSTTransformer):
        METADATA_DEPENDENCIES = (ParentNodeProvider, QualifiedNameProvider)

        def __init__(
            self,
            *,
            relative_imports: t.StrMapping,
            removals: t.MappingKV[str, frozenset[str]],
            obsolete_imports: t.MappingKV[str, frozenset[str]],
            replacements: t.StrMapping,
            public_imports: t.StrMapping,
        ) -> None:
            self.relative_imports = relative_imports
            self.removals = removals
            self.obsolete_imports = obsolete_imports
            self.replacements = replacements
            self.public_imports = dict(public_imports)

        @staticmethod
        def dotted_name(node: cst.BaseExpression | None) -> str | None:
            """Return a static dotted name or ``None`` for dynamic expressions."""
            if isinstance(node, cst.Name):
                return node.value
            if isinstance(node, cst.Attribute):
                parent = FlextInfraUtilitiesPrivateImportCst._Transformer.dotted_name(
                    node.value
                )
                return f"{parent}.{node.attr.value}" if parent else None
            return None

        @override
        def leave_Name(
            self, original_node: cst.Name, updated_node: cst.Name
        ) -> cst.BaseExpression:
            """Replace only names bound to one authenticated private identity."""
            targets = {
                replacement
                for qualified_name in self.get_metadata(
                    QualifiedNameProvider, original_node, ()
                )
                if (replacement := self.replacements.get(qualified_name.name))
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
            if isinstance(parent, cst.ImportAlias):
                return updated_node
            if isinstance(parent, cst.Attribute) and parent.attr is original_node:
                return updated_node
            if isinstance(parent, cst.Arg) and parent.keyword is original_node:
                return updated_node
            return cst.parse_expression(targets.pop())

        @override
        def leave_ImportFrom(
            self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
        ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
            """Relativize same-owner imports or remove cross-owner bindings."""
            module = self.dotted_name(original_node.module)
            module_name = module or ""
            relative_module = self.relative_imports.get(module_name)
            if relative_module is not None:
                relative_level = len(relative_module) - len(relative_module.lstrip("."))
                relative_name = relative_module[relative_level:]
                return updated_node.with_changes(
                    relative=tuple(cst.Dot() for _ in range(relative_level)),
                    module=(
                        cst.parse_expression(relative_name) if relative_name else None
                    ),
                )
            removed = self.removals.get(
                module_name, frozenset()
            ) | self.obsolete_imports.get(module_name, frozenset())
            canonical = {
                alias
                for alias, package in self.public_imports.items()
                if package == module_name
            }
            if isinstance(updated_node.names, cst.ImportStar) or (
                not removed and not canonical
            ):
                return updated_node
            retained = [
                imported
                for imported in updated_node.names
                if self.dotted_name(imported.name) not in removed
                and not (
                    self.dotted_name(imported.name) in canonical
                    and imported.asname is None
                )
            ]
            if retained:
                last_index = len(retained) - 1
                normalized: list[cst.ImportAlias] = []
                for index, imported in enumerate(retained):
                    if index == last_index and not updated_node.lpar:
                        normalized.append(
                            imported.with_changes(comma=cst.MaybeSentinel.DEFAULT)
                        )
                    elif index < last_index and not isinstance(
                        imported.comma, cst.Comma
                    ):
                        normalized.append(
                            imported.with_changes(
                                comma=cst.Comma(
                                    whitespace_after=cst.SimpleWhitespace(" ")
                                )
                            )
                        )
                    else:
                        normalized.append(imported)
                return updated_node.with_changes(names=tuple(normalized))
            return cst.RemoveFromParent()

    class _TypeCheckingImports(cst.CSTTransformer):
        """Insert one canonical group for facades used only by annotations."""

        def __init__(self, public_imports: t.StrMapping) -> None:
            self.public_imports = public_imports
            self.inserted = False

        @override
        def leave_If(self, original_node: cst.If, updated_node: cst.If) -> cst.If:
            """Populate the first explicit ``TYPE_CHECKING`` block."""
            if (
                self.inserted
                or not isinstance(original_node.test, cst.Name)
                or original_node.test.value != "TYPE_CHECKING"
            ):
                return updated_node
            if not isinstance(updated_node.body, cst.IndentedBlock):
                msg = "TYPE_CHECKING boundary must use an indented block"
                raise TypeError(msg)
            grouped: dict[str, list[str]] = {}
            for alias, package in sorted(self.public_imports.items()):
                grouped.setdefault(package, []).append(alias)
            imports = tuple(
                cst.parse_statement(f"from {package} import {', '.join(aliases)}\n")
                for package, aliases in sorted(grouped.items())
            )
            self.inserted = True
            return updated_node.with_changes(
                body=updated_node.body.with_changes(
                    body=imports + tuple(updated_node.body.body)
                )
            )

    @classmethod
    def rewrite_private_import_source(
        cls,
        source: str,
        *,
        relative_imports: t.StrMapping,
        removals: t.MappingKV[str, frozenset[str]],
        obsolete_imports: t.MappingKV[str, frozenset[str]],
        replacements: t.StrMapping,
        public_imports: t.StrMapping,
        runtime_public_imports: frozenset[str],
    ) -> str:
        """Return a binding-proven rewrite with required public imports."""
        transformer = cls._Transformer(
            relative_imports=relative_imports,
            removals=removals,
            obsolete_imports=obsolete_imports,
            replacements=replacements,
            public_imports=public_imports,
        )
        rewritten = MetadataWrapper(cst.parse_module(source)).visit(transformer)
        context = CodemodContext()
        for facade_alias in sorted(runtime_public_imports):
            package = public_imports[facade_alias]
            AddImportsVisitor.add_needed_import(context, package, facade_alias)
        rewritten = rewritten.visit(AddImportsVisitor(context))
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
        return rewritten.code


__all__: list[str] = ["FlextInfraUtilitiesPrivateImportCst"]
