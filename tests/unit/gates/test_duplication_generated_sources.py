"""Duplication gate excludes generated projections from clone findings.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pathlib as pl
from typing import ClassVar

from flext_infra import t
from flext_infra.gates import FlextInfraDuplicationReport
from tests import tm


class TestsDuplicationGeneratedSources(FlextInfraDuplicationReport):
    """Generated sources are owned by their generator, not clone analysis."""

    gate_id: ClassVar[str] = "duplication"

    @classmethod
    def test_recognizes_the_generated_marker_on_the_first_line(
        cls,
        tmp_path: pl.Path,
    ) -> None:
        """The generator's first-line marker identifies a generated source."""
        generated = tmp_path / "generated.py"
        generated.write_text(
            "# AUTO-GENERATED FILE — Regenerate with: make gen\nvalue = 1\n",
            encoding="utf-8",
        )
        authored = tmp_path / "authored.py"
        authored.write_text("value = 1\n", encoding="utf-8")

        tm.that(cls._is_generated_source(generated) is True, truth=True)
        tm.that(cls._is_generated_source(authored) is False, truth=True)

    @classmethod
    def test_generated_side_is_never_an_owned_clone_finding(
        cls,
        tmp_path: pl.Path,
    ) -> None:
        """A clone touching a generated projection is not a finding."""
        generated = tmp_path / "generated.py"
        generated.write_text(
            "# AUTO-GENERATED FILE — Regenerate with: make gen\nvalue = 1\n",
            encoding="utf-8",
        )
        authored = tmp_path / "authored.py"
        authored.write_text("value = 1\n", encoding="utf-8")
        other = tmp_path / "other.py"
        other.write_text("value = 1\n", encoding="utf-8")

        generated_clone: t.JsonMapping = {
            "firstFile": {
                "name": str(generated),
                "startLoc": {"line": 1, "column": 0},
                "endLoc": {"line": 2, "column": 0},
            },
            "secondFile": {
                "name": str(authored),
                "startLoc": {"line": 1, "column": 0},
                "endLoc": {"line": 2, "column": 0},
            },
            "lines": 2,
        }
        authored_clone: t.JsonMapping = {
            "firstFile": {
                "name": str(authored),
                "startLoc": {"line": 1, "column": 0},
                "endLoc": {"line": 2, "column": 0},
            },
            "secondFile": {
                "name": str(other),
                "startLoc": {"line": 1, "column": 0},
                "endLoc": {"line": 2, "column": 0},
            },
            "lines": 2,
        }

        tm.that(cls._owned_clone_issue(generated_clone, tmp_path), eq=None)
        tm.that(
            cls._owned_clone_issue(authored_clone, tmp_path) is not None, truth=True
        )
