"""Pure AST traversal primitives of the rope family.

Importing nothing from ``_rope`` keeps this module a true family leaf: runtime
members load it at module top level and analysis members inherit it, so both
sides share one parent-map SSOT without an import cycle.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import MutableMapping
from typing import TypeGuard

from flext_infra import p


class FlextInfraUtilitiesRopeAst:
    """Family-leaf AST identity, narrowing and parent-lookup primitives."""

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
