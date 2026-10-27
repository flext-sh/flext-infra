"""Shared source fixtures and planning helpers for class-nesting owner derivation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from flext_infra import infra
from tests import c, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraClassNestingSupport:
    """Loose-module fixtures and the planning helpers the nesting contracts share."""

    LOOSE_MODULE = '''"""Loose helpers of one family module."""

from __future__ import annotations

import os

# Owner-only permission bits.
_MODE = 0o600
LIMIT: int = 3


class _Marker:
    """Marker for callers without a precondition."""


_SENTINEL = _Marker()


def write(path: str, marker: _Marker = _SENTINEL) -> int:
    """Return a size derived from ``path`` for an unmarked call."""
    if isinstance(marker, _Marker):
        return _helper(path) + _MODE
    return LIMIT


def _helper(path: str) -> int:
    return len(os.fspath(path))


__all__: list[str] = ["LIMIT", "write"]
'''

    @staticmethod
    def _family_module(tmp_path: Path, stem: str, source: str) -> t.Pair[Path, Path]:
        """Write one module into the utilities family package of a workspace.

        Returns:
            The repository root and the written module path.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = (
            package / u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        )
        tm.ok(u.Cli.ensure_dir(family))
        tm.ok(u.Cli.atomic_write_text_file(family / "__init__.py", ""))
        module = family / f"{stem}.py"
        tm.ok(u.Cli.atomic_write_text_file(module, source))
        return root, module

    @staticmethod
    def _derived_owner(root: Path, stem: str) -> str:
        """Return the owner the project class stem and family suffix derive.

        Returns:
            The derived owner class name.

        """
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        return (
            f"{u.derive_class_stem(root.name)}{family.suffix}"
            f"{u.derive_class_stem(stem)}"
        )

    @staticmethod
    def _plan(
        root: Path,
        sources: t.MappingKV[Path, str],
    ) -> t.Pair[t.MappingKV[Path, str], t.MappingKV[Path, str] | str]:
        """Plan class nesting, then replan the planned sources.

        Returns:
            The planned sources and the replanned residue (or its failure).

        """
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources=sources,
            )
            tm.ok(planned)
            updated = dict(sources)
            updated.update(
                (edit.file_path, edit.updated_source) for edit in planned.value
            )
            replanned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources=updated,
            )
        residue = (
            replanned.error or ""
            if replanned.failure
            else {edit.file_path: edit.updated_source for edit in replanned.value}
        )
        return updated, residue

    @staticmethod
    def _top_level(source: str) -> t.VariadicTuple[str]:
        """Return the names a module binds at top level, imports excluded.

        Returns:
            The class, function and assignment names in source order.

        """
        names: list[str] = []
        for node in ast.parse(source).body:
            if isinstance(node, ast.ClassDef | ast.FunctionDef):
                names.append(node.name)
            elif isinstance(node, c.Infra.AST_ASSIGNMENT_TYPES):
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
                names.extend(
                    target.id for target in targets if isinstance(target, ast.Name)
                )
        return tuple(names)
