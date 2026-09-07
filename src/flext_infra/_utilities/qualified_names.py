"""LibCST qualified-name metadata utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import libcst as cst
from libcst.metadata import MetadataWrapper, QualifiedNameProvider

if TYPE_CHECKING:
    from flext_infra.protocols import p
    from flext_infra.typings import t


class FlextInfraUtilitiesQualifiedNames:
    """Resolve lazy LibCST qualified-name metadata through its public visitor API."""

    class _ResidueCollector(cst.CSTVisitor):
        METADATA_DEPENDENCIES = (QualifiedNameProvider,)

        def __init__(self, candidates: t.Infra.Container[str]) -> None:
            self.candidates = candidates
            self.residue: set[str] = set()

        @override
        def on_visit(self, node: cst.CSTNode) -> bool:
            self.residue.update(
                qualified_name.name
                for qualified_name in self.get_metadata(QualifiedNameProvider, node, ())
                if qualified_name.name in self.candidates
            )
            return True

    @staticmethod
    def rebinds_name_in_place(parent: p.AttributeProbe, node: cst.CSTNode) -> bool:
        """Return whether ``parent`` spells ``node`` as a binding, not a reference.

        An import alias, an attribute's own ``attr``, and a keyword argument's
        name are written by the surrounding syntax, so a rename must leave them
        exactly as they are.
        """
        if isinstance(parent, cst.ImportAlias):
            return True
        if isinstance(parent, cst.Attribute) and parent.attr is node:
            return True
        return isinstance(parent, cst.Arg) and parent.keyword is node

    @classmethod
    def qualified_name_residue(
        cls, source: str, candidates: t.Infra.Container[str]
    ) -> frozenset[str]:
        """Return candidate qualified names referenced by Python source."""
        collector = cls._ResidueCollector(candidates)
        MetadataWrapper(cst.parse_module(source)).visit(collector)
        return frozenset(collector.residue)


__all__: list[str] = ["FlextInfraUtilitiesQualifiedNames"]
