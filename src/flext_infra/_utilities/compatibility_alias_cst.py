"""Concrete-syntax rewrites for compatibility-alias cutovers."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import libcst as cst
from libcst.metadata import MetadataWrapper, ParentNodeProvider, QualifiedNameProvider

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraUtilitiesCompatibilityAliasCst:
    """Preserve formatting while alias ownership is cut over."""

    class _Transformer(cst.CSTTransformer):
        METADATA_DEPENDENCIES = (ParentNodeProvider, QualifiedNameProvider)

        def __init__(
            self,
            *,
            local_aliases: t.StrMapping,
            import_aliases: t.MappingKV[str, t.StrMapping],
            attribute_aliases: t.MappingKV[t.Pair[str, str], str],
            qualified_aliases: t.StrMapping,
            target_bindings: frozenset[str],
        ) -> None:
            self.local_aliases = local_aliases
            self.import_aliases = import_aliases
            self.attribute_aliases = attribute_aliases
            self.qualified_aliases = qualified_aliases
            self.target_bindings = target_bindings

        @staticmethod
        def dotted_name(node: cst.BaseExpression | None) -> str | None:
            if isinstance(node, cst.Name):
                return node.value
            if isinstance(node, cst.Attribute):
                parent = (
                    FlextInfraUtilitiesCompatibilityAliasCst._Transformer.dotted_name(
                        node.value
                    )
                )
                return f"{parent}.{node.attr.value}" if parent else None
            return None

        @staticmethod
        def _without_exports(
            value: cst.BaseExpression, aliases: frozenset[str]
        ) -> cst.BaseExpression:
            if not isinstance(value, cst.List | cst.Tuple):
                return value
            retained = [
                element
                for element in value.elements
                if not isinstance(element.value, cst.SimpleString)
                or not isinstance(element.value.evaluated_value, str)
                or element.value.evaluated_value not in aliases
            ]
            return value.with_changes(elements=retained)

        @override
        def leave_Name(
            self, original_node: cst.Name, updated_node: cst.Name
        ) -> cst.Name:
            targets = {
                target
                for qualified_name in self.get_metadata(
                    QualifiedNameProvider, original_node, ()
                )
                if (target := self.qualified_aliases.get(qualified_name.name))
                is not None
            }
            if not targets:
                return updated_node
            if len(targets) != 1:
                msg = f"ambiguous qualified alias {original_node.value}: {sorted(targets)}"
                raise ValueError(msg)
            parent = self.get_metadata(ParentNodeProvider, original_node)
            if isinstance(parent, cst.ImportAlias):
                return updated_node
            if isinstance(parent, cst.Attribute) and parent.attr is original_node:
                return updated_node
            if isinstance(parent, cst.Arg) and parent.keyword is original_node:
                return updated_node
            return updated_node.with_changes(value=targets.pop())

        @override
        def leave_Assign(
            self, original_node: cst.Assign, updated_node: cst.Assign
        ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
            if (
                len(original_node.targets) == 1
                and isinstance(original_node.targets[0].target, cst.Name)
                and isinstance(original_node.value, cst.Name)
            ):
                alias = original_node.targets[0].target.value
                if self.local_aliases.get(alias) == original_node.value.value:
                    return cst.RemoveFromParent()
            if (
                len(original_node.targets) == 1
                and isinstance(original_node.targets[0].target, cst.Name)
                and original_node.targets[0].target.value == "__all__"
            ):
                return updated_node.with_changes(
                    value=self._without_exports(
                        updated_node.value, frozenset(self.local_aliases)
                    )
                )
            return updated_node

        @override
        def leave_AnnAssign(
            self, original_node: cst.AnnAssign, updated_node: cst.AnnAssign
        ) -> cst.BaseSmallStatement:
            if (
                isinstance(original_node.target, cst.Name)
                and original_node.target.value == "__all__"
                and updated_node.value is not None
            ):
                return updated_node.with_changes(
                    value=self._without_exports(
                        updated_node.value, frozenset(self.local_aliases)
                    )
                )
            return updated_node

        @override
        def leave_ImportFrom(
            self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
        ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
            rewrites = self.import_aliases.get(
                self.dotted_name(original_node.module) or ""
            )
            if not rewrites or isinstance(updated_node.names, cst.ImportStar):
                return updated_node
            retained: list[cst.ImportAlias] = []
            for imported in updated_node.names:
                name = self.dotted_name(imported.name)
                target = rewrites.get(name or "")
                if target is None:
                    retained.append(imported)
                elif imported.asname is None and target in self.target_bindings:
                    continue
                else:
                    retained.append(imported.with_changes(name=cst.Name(target)))
            return (
                updated_node.with_changes(names=retained)
                if retained
                else cst.RemoveFromParent()
            )

        @override
        def leave_Attribute(
            self, original_node: cst.Attribute, updated_node: cst.Attribute
        ) -> cst.BaseExpression:
            owner = self.dotted_name(original_node.value) or ""
            target = self.attribute_aliases.get((owner, original_node.attr.value))
            return (
                updated_node.with_changes(attr=cst.Name(target))
                if target
                else updated_node
            )

    @classmethod
    def rewrite_compatibility_alias_source(
        cls,
        source: str,
        *,
        local_aliases: t.StrMapping,
        import_aliases: t.MappingKV[str, t.StrMapping],
        attribute_aliases: t.MappingKV[t.Pair[str, str], str],
        qualified_aliases: t.StrMapping,
        target_bindings: frozenset[str],
    ) -> str:
        """Return the structurally rewritten source without changing its layout."""
        return (
            MetadataWrapper(cst.parse_module(source))
            .visit(
                cls._Transformer(
                    local_aliases=local_aliases,
                    import_aliases=import_aliases,
                    attribute_aliases=attribute_aliases,
                    qualified_aliases=qualified_aliases,
                    target_bindings=target_bindings,
                )
            )
            .code
        )


__all__: list[str] = ["FlextInfraUtilitiesCompatibilityAliasCst"]
