"""The generator recognizes its projections by the stable marker, not the full header.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraAutogenMarker:
    """A header rewritten by ADR-037 keeps every earlier projection generated."""

    @staticmethod
    def test_header_names_make_check() -> None:
        """The header the generator writes tells the reader to run make check."""
        tm.that(c.Infra.AUTOGEN_HEADER.startswith(c.Infra.AUTOGEN_MARKER), eq=True)
        tm.that(c.Infra.AUTOGEN_HEADER.endswith("make check"), eq=True)

    @staticmethod
    def test_earlier_header_stays_a_generated_projection(tmp_path: Path) -> None:
        """A file still carrying the pre-ADR-037 header is generated, not authored."""
        anterior = f"{c.Infra.AUTOGEN_MARKER}Regenerate with: make gen\n"
        arquivo = tmp_path / "__init__.py"
        arquivo.write_text(anterior + "x = 1\n", encoding=c.DEFAULT_ENCODING)
        tm.that(u.Infra.generated_source(arquivo), eq=True)
        tm.that(
            u.Infra.codegen_initializer_is_authored(
                arquivo.read_bytes(),
            ),
            eq=False,
        )

    @staticmethod
    def test_authored_file_is_not_generated(tmp_path: Path) -> None:
        """A file without the marker belongs to its author."""
        arquivo = tmp_path / "__init__.py"
        arquivo.write_text('"""Authored."""\n', encoding=c.DEFAULT_ENCODING)
        tm.that(u.Infra.generated_source(arquivo), eq=False)
        tm.that(
            u.Infra.codegen_initializer_is_authored(arquivo.read_bytes()),
            eq=True,
        )
