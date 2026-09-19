"""Concrete-syntax rewrites for compatibility-alias cutovers."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import libcst as cst
from libcst.metadata import MetadataWrapper, ParentNodeProvider, QualifiedNameProvider

from ..qualified_names import FlextInfraUtilitiesQualifiedNames

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraUtilitiesSemanticCutoverAliasCst:
    """Preserve formatting while alias ownership is cut over."""

    class _AliasTransformer(cst.CSTTransformer):
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
            if FlextInfraUtilitiesQualifiedNames.rebinds_name_in_place(
                parent, original_node
            ):
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
                and self.local_aliases.get(original_node.targets[0].target.value)
                == original_node.value.value
            ):
                return cst.RemoveFromParent()
            return FlextInfraUtilitiesQualifiedNames.filter_exports(
                updated_node, self.local_aliases
            )

        @override
        def leave_AnnAssign(
            self, original_node: cst.AnnAssign, updated_node: cst.AnnAssign
        ) -> cst.BaseSmallStatement:
            return FlextInfraUtilitiesQualifiedNames.filter_exports(
                updated_node, self.local_aliases
            )

        @override
        def leave_ImportFrom(
            self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
        ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
            rewrites = self.import_aliases.get(
                FlextInfraUtilitiesQualifiedNames.dotted_name(original_node.module)
                or ""
            )
            if not rewrites or isinstance(updated_node.names, cst.ImportStar):
                return updated_node
            retained: list[cst.ImportAlias] = []
            for imported in updated_node.names:
                target = rewrites.get(
                    FlextInfraUtilitiesQualifiedNames.dotted_name(imported.name) or ""
                )
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
            owner = (
                FlextInfraUtilitiesQualifiedNames.dotted_name(original_node.value) or ""
            )
            target = self.attribute_aliases.get((owner, original_node.attr.value))
            return (
                updated_node.with_changes(attr=cst.Name(target))
                if target
                else updated_node
            )

    @classmethod
    def _rewrite_compatibility_alias_source(
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
                cls._AliasTransformer(
                    local_aliases=local_aliases,
                    import_aliases=import_aliases,
                    attribute_aliases=attribute_aliases,
                    qualified_aliases=qualified_aliases,
                    target_bindings=target_bindings,
                )
            )
            .code
        )


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverAliasCst"]
