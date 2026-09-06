"""Binding-aware reference rewrites for automatic class nesting."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import libcst as cst
from libcst.metadata import MetadataWrapper, ParentNodeProvider, QualifiedNameProvider

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraUtilitiesClassNestingReferences:
    """Rewrite imports and usages of classes moved below a module owner."""

    class _Transformer(cst.CSTTransformer):
        METADATA_DEPENDENCIES = (ParentNodeProvider, QualifiedNameProvider)

        def __init__(
            self,
            *,
            module_name: str,
            is_package_init: bool,
            bindings_by_module: t.MappingKV[str, t.StrMapping],
            definitions: t.StrMapping,
        ) -> None:
            self.module_name = module_name
            self.is_package_init = is_package_init
            self.bindings_by_module = bindings_by_module
            self.definitions = definitions
            self.qualified = {
                f"{module}.{name}": f"{owner}.{name}"
                for module, bindings in bindings_by_module.items()
                for name, owner in bindings.items()
            }
            self.qualified.update(
                (name, f"{owner}.{name}") for name, owner in definitions.items()
            )
            self.local_expressions: dict[str, str] = {
                name: f"{owner}.{name}" for name, owner in definitions.items()
            }

        def _dotted_name(self, node: cst.BaseExpression | None) -> str | None:
            if isinstance(node, cst.Name):
                return node.value
            if isinstance(node, cst.Attribute):
                parent = self._dotted_name(node.value)
                return f"{parent}.{node.attr.value}" if parent else None
            return None

        def _import_module(self, node: cst.ImportFrom) -> str:
            suffix = self._dotted_name(node.module) or ""
            if not node.relative:
                return suffix
            package_parts = self.module_name.split(".")
            if not self.is_package_init:
                package_parts = package_parts[:-1]
            ascend = len(node.relative) - 1
            if ascend > len(package_parts):
                return ""
            prefix = package_parts[: len(package_parts) - ascend]
            return ".".join((*prefix, suffix) if suffix else prefix)

        @override
        def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
            bindings = self.bindings_by_module.get(self._import_module(node), {})
            if not bindings or isinstance(node.names, cst.ImportStar):
                return
            for imported in node.names:
                name = self._dotted_name(imported.name) or ""
                if name not in bindings:
                    continue
                local_name = imported.asname.name.value if imported.asname else name
                owner_name = local_name if imported.asname else bindings[name]
                self.local_expressions[local_name] = f"{owner_name}.{name}"

        @staticmethod
        def _is_structural_position(
            parent: cst.CSTNode, original_node: cst.Name
        ) -> bool:
            """Whether the name occupies a structural position, not a value use."""
            if isinstance(parent, cst.ImportAlias):
                return True
            if isinstance(parent, cst.ClassDef):
                return parent.name is original_node
            if isinstance(parent, cst.Attribute):
                return parent.attr is original_node
            if isinstance(parent, cst.Arg):
                return parent.keyword is original_node
            return False

        @override
        def leave_Name(
            self, original_node: cst.Name, updated_node: cst.Name
        ) -> cst.BaseExpression:
            replacements = {
                replacement
                for qualified_name in self.get_metadata(
                    QualifiedNameProvider, original_node, ()
                )
                if (replacement := self.qualified.get(qualified_name.name)) is not None
            }
            if not replacements:
                return updated_node
            if len(replacements) != 1:
                msg = f"ambiguous class-nesting binding: {sorted(replacements)}"
                raise ValueError(msg)
            parent = self.get_metadata(ParentNodeProvider, original_node)
            if self._is_structural_position(parent, original_node):
                return updated_node
            replacement = self.local_expressions.get(original_node.value)
            if replacement is None:
                replacement = next(iter(replacements))
            return cst.parse_expression(replacement)

        @override
        def leave_Attribute(
            self, original_node: cst.Attribute, updated_node: cst.Attribute
        ) -> cst.BaseExpression:
            replacements = {
                replacement
                for qualified_name in self.get_metadata(
                    QualifiedNameProvider, original_node, ()
                )
                if (replacement := self.qualified.get(qualified_name.name)) is not None
            }
            if not replacements:
                return updated_node
            if len(replacements) != 1:
                msg = f"ambiguous class-nesting attribute: {sorted(replacements)}"
                raise ValueError(msg)
            owner, name = replacements.pop().split(".", maxsplit=1)
            return cst.Attribute(
                value=cst.Attribute(value=updated_node.value, attr=cst.Name(owner)),
                attr=cst.Name(name),
            )

        @override
        def leave_ImportFrom(
            self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
        ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
            bindings = self.bindings_by_module.get(
                self._import_module(original_node), {}
            )
            if not bindings or isinstance(updated_node.names, cst.ImportStar):
                return updated_node
            aliases: list[cst.ImportAlias] = []
            seen: set[tuple[str, str]] = set()
            for imported in updated_node.names:
                name = self._dotted_name(imported.name) or ""
                owner = bindings.get(name)
                rewritten = (
                    imported.with_changes(name=cst.Name(owner)) if owner else imported
                )
                identity = (
                    self._dotted_name(rewritten.name) or "",
                    rewritten.asname.name.value if rewritten.asname else "",
                )
                if identity not in seen:
                    seen.add(identity)
                    aliases.append(rewritten)
            if not aliases:
                return cst.RemoveFromParent()
            if not updated_node.lpar:
                aliases = [
                    alias.with_changes(
                        comma=(
                            cst.MaybeSentinel.DEFAULT
                            if index == len(aliases) - 1
                            else cst.Comma(whitespace_after=cst.SimpleWhitespace(" "))
                        )
                    )
                    for index, alias in enumerate(aliases)
                ]
            return updated_node.with_changes(names=tuple(aliases))

        def _without_nested_exports(
            self, value: cst.BaseExpression
        ) -> cst.BaseExpression:
            if not isinstance(value, cst.List | cst.Tuple):
                return value
            names = frozenset(self.definitions)
            return value.with_changes(
                elements=tuple(
                    element
                    for element in value.elements
                    if not isinstance(element.value, cst.SimpleString)
                    or element.value.evaluated_value not in names
                )
            )

        @override
        def leave_Assign(
            self, original_node: cst.Assign, updated_node: cst.Assign
        ) -> cst.BaseSmallStatement:
            if not (
                len(original_node.targets) == 1
                and isinstance(original_node.targets[0].target, cst.Name)
                and original_node.targets[0].target.value == "__all__"
            ):
                return updated_node
            return updated_node.with_changes(
                value=self._without_nested_exports(updated_node.value)
            )

        @override
        def leave_AnnAssign(
            self, original_node: cst.AnnAssign, updated_node: cst.AnnAssign
        ) -> cst.BaseSmallStatement:
            if not (
                isinstance(original_node.target, cst.Name)
                and original_node.target.value == "__all__"
                and updated_node.value is not None
            ):
                return updated_node
            return updated_node.with_changes(
                value=self._without_nested_exports(updated_node.value)
            )

    @classmethod
    def rewrite_class_nesting_references(
        cls,
        source: str,
        *,
        module_name: str,
        is_package_init: bool,
        bindings_by_module: t.MappingKV[str, t.StrMapping],
        definitions: t.StrMapping,
    ) -> str:
        """Return binding-proven import and usage rewrites without effects."""
        return (
            MetadataWrapper(cst.parse_module(source))
            .visit(
                cls._Transformer(
                    module_name=module_name,
                    is_package_init=is_package_init,
                    bindings_by_module=bindings_by_module,
                    definitions=definitions,
                )
            )
            .code
        )


__all__: list[str] = ["FlextInfraUtilitiesClassNestingReferences"]
