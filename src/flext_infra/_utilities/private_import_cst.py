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
            removals: t.MappingKV[str, frozenset[str]],
            replacements: t.StrMapping,
            public_imports: t.StrMapping,
        ) -> None:
            self.removals = removals
            self.replacements = replacements
            self.public_imports = {alias: package for package, alias in public_imports.items()}
            self.inserted_public_imports: set[tuple[str, str]] = set()
            self.global_public_imports: set[tuple[str, str]] = set()

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
                if (
                    replacement := self.replacements.get(qualified_name.name)
                )
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
            """Remove migrated symbols from their exact private import."""
            module = self.dotted_name(original_node.module)
            removed = self.removals.get(module or "")
            if not removed or isinstance(updated_node.names, cst.ImportStar):
                return updated_node
            retained = [
                imported
                for imported in updated_node.names
                if self.dotted_name(imported.name) not in removed
            ]
            targets = {
                (package, alias)
                for imported in original_node.names
                if (symbol := self.dotted_name(imported.name)) in removed
                and (
                    reference := self.replacements.get(f"{module}.{symbol}")
                )
                is not None
                and (alias := reference.split(".", 1)[0]) in self.public_imports
                and (package := self.public_imports[alias])
            }
            if retained:
                self.global_public_imports.update(targets)
                return updated_node.with_changes(names=retained)
            if len(targets) == 1:
                package, alias = targets.pop()
                self.inserted_public_imports.add((package, alias))
                return updated_node.with_changes(
                    module=cst.parse_expression(package),
                    names=(cst.ImportAlias(name=cst.Name(alias)),),
                )
            self.global_public_imports.update(targets)
            return cst.RemoveFromParent()

    @classmethod
    def rewrite_private_import_source(
        cls,
        source: str,
        *,
        removals: t.MappingKV[str, frozenset[str]],
        replacements: t.StrMapping,
        public_imports: t.StrMapping,
    ) -> str:
        """Return a binding-proven rewrite with required public imports."""
        transformer = cls._Transformer(
            removals=removals,
            replacements=replacements,
            public_imports=public_imports,
        )
        rewritten = MetadataWrapper(cst.parse_module(source)).visit(transformer)
        context = CodemodContext()
        for package, facade_alias in sorted(public_imports.items()):
            target = (package, facade_alias)
            if (
                target in transformer.inserted_public_imports
                and target not in transformer.global_public_imports
            ):
                continue
            AddImportsVisitor.add_needed_import(context, package, facade_alias)
        return rewritten.visit(AddImportsVisitor(context)).code


__all__: list[str] = ["FlextInfraUtilitiesPrivateImportCst"]
