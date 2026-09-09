"""LibCST qualified-name metadata utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import libcst as cst
from libcst.metadata import (
    MetadataWrapper,
    PositionProvider,
    QualifiedNameProvider,
    QualifiedNameSource,
)

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

    class _CallableCollector(cst.CSTVisitor):
        METADATA_DEPENDENCIES = (PositionProvider, QualifiedNameProvider)

        def __init__(self, source: str) -> None:
            self.lines = source.splitlines()
            self.names: dict[tuple[int, int], frozenset[str]] = {}

        def _collect(self, node: cst.BaseExpression) -> None:
            if not isinstance(node, (cst.Name, cst.Attribute)):
                return
            location = self.get_metadata(PositionProvider, node)
            position = location.start
            # Python AST columns count UTF-8 bytes; LibCST columns count characters.
            column = len(self.lines[position.line - 1][: position.column].encode())
            self.names[position.line, column] = frozenset(
                name.name
                for name in self.get_metadata(QualifiedNameProvider, node, ())
                if name.source is QualifiedNameSource.IMPORT
            )

        @override
        def visit_Call(self, node: cst.Call) -> None:
            self._collect(node.func)

        @override
        def visit_Decorator(self, node: cst.Decorator) -> None:
            if not isinstance(node.decorator, cst.Call):
                self._collect(node.decorator)

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

    @classmethod
    def imported_callable_names(
        cls, source: str
    ) -> t.MappingKV[t.Pair[int, int], frozenset[str]]:
        """Resolve call/decorator import provenance at Python AST source positions."""
        collector = cls._CallableCollector(source)
        MetadataWrapper(cst.parse_module(source)).visit(collector)
        return collector.names


__all__: list[str] = ["FlextInfraUtilitiesQualifiedNames"]
