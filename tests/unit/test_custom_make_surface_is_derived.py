"""Tests that the custom Make surface name is derived, never re-typed.

``c.Infra.CUSTOM_MAKE_FILENAME`` is the SSOT for the custom Make surface. Any
module that re-types the literal ``custom.mk`` forks that SSOT: renaming the
surface then requires a manual sweep across the engine, and a missed site
silently emits a Makefile that includes a file nobody generates.

The engine must therefore *derive* every occurrence — include directives,
generated headers and docstring-free code paths alike — from the constant.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

import flext_infra
from flext_tests import tm

from flext_infra import c


def _engine_modules() -> tuple[Path, ...]:
    """Return every shipped engine module, excluding the template tree."""
    root = Path(flext_infra.__file__).resolve().parent
    templates = root / "templates"
    return tuple(
        sorted(path for path in root.rglob("*.py") if templates not in path.parents)
    )


def _string_literals(module: Path) -> tuple[str, ...]:
    """Return every string literal in *module*, excluding docstrings."""
    tree = ast.parse(module.read_text(encoding="utf-8"))
    docstrings = {
        ast.get_docstring(node, clean=False)
        for node in ast.walk(tree)
        if isinstance(
            node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        )
    }
    return tuple(
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value not in docstrings
    )


class TestsFlextInfraCustomMakeSurfaceIsDerived:
    def test_include_directive_is_derived_from_the_filename_ssot(self) -> None:
        """The include directive embeds the SSOT filename, not a copy of it."""
        tm.that(
            c.Infra.MAKEFILE_CUSTOM_INCLUDE.endswith(c.Infra.CUSTOM_MAKE_FILENAME),
            eq=True,
        )

    def test_no_engine_module_retypes_the_custom_surface_literal(self) -> None:
        """Only the constants SSOT may contain the literal filename."""
        ssot = Path(flext_infra.__file__).resolve().parent / "_constants"
        offenders = sorted(
            str(module.relative_to(Path(flext_infra.__file__).resolve().parent))
            for module in _engine_modules()
            if ssot not in module.parents
            and any(
                c.Infra.CUSTOM_MAKE_FILENAME in literal
                for literal in _string_literals(module)
            )
        )

        tm.that(offenders, eq=[])
