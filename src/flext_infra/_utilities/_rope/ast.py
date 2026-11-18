"""Pure AST traversal primitives of the rope family.

Importing nothing from ``_rope`` keeps this module a true family leaf: runtime
members load it at module top level and analysis members inherit it, so both
sides share one parent-map SSOT without an import cycle.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import io
import tokenize
from collections.abc import Mapping, MutableMapping
from functools import cache
from typing import TypeGuard

from flext_infra import p


@cache
def _name_offset_index(source: str) -> Mapping[str, tuple[int, ...]]:
    """Index every complete NAME token by its absolute source offset.

    Returns:
        The offset tuple of each complete NAME token in ``source``.

    """
    line_starts = [0]
    for line in source.splitlines(keepends=True):
        line_starts.append(line_starts[-1] + len(line))
    offsets: MutableMapping[str, list[int]] = {}
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.NAME:
            row, column = token.start
            offsets.setdefault(token.string, []).append(line_starts[row - 1] + column)
    return {name: tuple(values) for name, values in offsets.items()}


class FlextInfraUtilitiesRopeAst:
    """Family-leaf AST identity, narrowing and parent-lookup primitives."""

    @staticmethod
    def name_offsets(source: str, name: str) -> tuple[int, ...]:
        """Return every complete NAME-token offset of ``name`` in ``source``.

        Returns:
            The absolute offsets where ``name`` is a complete identifier token.

        """
        return _name_offset_index(source).get(name, ())

    @staticmethod
    def ast_node(obj: p.AttributeProbe) -> TypeGuard[ast.AST]:
        """Narrow a rope-provided object to a native ``ast.AST`` node.

        Returns:
            The resulting ``TypeGuard[ast.AST]``.

        """
        return isinstance(obj, ast.AST)

    @staticmethod
    def ensure_ast_node(obj: p.AttributeProbe) -> ast.AST:
        """Ensure an object is an AST node, narrowing the type.

        Returns:
            The resulting ``ast.AST``.

        Raises:
            TypeError: If Expected AST node, got.

        """
        if not FlextInfraUtilitiesRopeAst.ast_node(obj):
            msg = f"Expected AST node, got {type(obj).__name__}"
            raise TypeError(msg)
        return obj

    @staticmethod
    def ast_parent_map(
        root: p.AttributeProbe,
    ) -> MutableMapping[int, ast.AST]:
        """Return a child-id -> parent map for the full AST reachable from ``root``.

        The shared SSOT for parent lookups across every rope detector. The
        walk visits native ``ast.AST`` nodes, so the map values keep that
        exact vocabulary.

        Returns:
            A child-id -> parent map for the full AST reachable from ``root``.

        """
        parent_map: MutableMapping[int, ast.AST] = {}
        if not isinstance(root, ast.AST):
            return parent_map
        for parent in ast.walk(root):
            owner = FlextInfraUtilitiesRopeAst.ensure_ast_node(parent)
            for child in ast.iter_child_nodes(parent):
                parent_map[id(child)] = owner
        return parent_map


__all__: list[str] = ["FlextInfraUtilitiesRopeAst"]
