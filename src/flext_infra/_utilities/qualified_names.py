"""LibCST qualified-name metadata utilities.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import libcst as cst
from libcst.metadata import (
    MetadataWrapper,
    QualifiedName,
    QualifiedNameProvider,
    QualifiedNameSource,
)

from flext_infra import t

if TYPE_CHECKING:
    from collections.abc import Container

    from flext_infra import p


class FlextInfraUtilitiesQualifiedNames:
    """Resolve lazy LibCST qualified-name metadata through its public visitor API."""

    @staticmethod
    def lexical_root(node: t.Infra.Cst.CSTNode) -> t.Infra.Cst.CSTNode:
        """Return the lexical receiver underlying a dotted attribute expression.

        Returns:
            The leftmost receiver node.

        """
        while isinstance(node, t.Infra.Cst.Attribute):
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
        if isinstance(node, t.Infra.Cst.Name):
            return node.value
        if isinstance(node, t.Infra.Cst.Attribute):
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
        if not isinstance(value, t.Infra.Cst.List | t.Infra.Cst.Tuple):
            return value
        return value.with_changes(
            elements=tuple(
                element
                for element in value.elements
                if not isinstance(element.value, t.Infra.Cst.SimpleString)
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
            if isinstance(node, t.Infra.Cst.Assign)
            else (node.target,)
        )
        if (
            len(targets) != 1
            or not isinstance(targets[0], t.Infra.Cst.Name)
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
            if index < last_index and not isinstance(alias.comma, t.Infra.Cst.Comma)
            else alias
            for index, alias in enumerate(aliases)
        )

    @staticmethod
    def rebinds_name_in_place(parent: p.AttributeProbe, node: t.Infra.Cst.CSTNode) -> bool:
        """Return whether ``parent`` spells ``node`` as a binding, not a reference.

        An import alias, an attribute's own ``attr``, and a keyword argument's
         name are written by the surrounding syntax, so a rename must leave them
         exactly as they are.

        Returns:
            Whether ``parent`` spells ``node`` as a binding, not a reference.

        """
        if isinstance(parent, t.Infra.Cst.ImportAlias):
            return True
        if isinstance(parent, t.Infra.Cst.Attribute) and parent.attr is node:
            return True
        return isinstance(parent, t.Infra.Cst.Arg) and parent.keyword is node

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
                if isinstance(node, t.Infra.Cst.Attribute) and any(
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
