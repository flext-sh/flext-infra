"""Tests for u facade.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from tests.utilities import u


class TestsFlextInfraInfraUtilities:
    """Test u class import and structure."""

    def test_extract_definition_keeps_multiline_class_header_intact(self) -> None:
        """Multi-line class headers must keep their closing line during extraction."""
        source = (
            "class ExamplesFlextModels(\n"
            "    m,\n"
            "):\n"
            '    """Doc."""\n'
            "\n"
            "    class Examples:\n"
            "        pass\n"
        )

        block = u.Infra.extract_definition(
            source,
            "ExamplesFlextModels",
            kind="class",
        )

        assert u.Infra.bracket_balance_line("class ExamplesFlextModels(") == 1
        assert block == source.rstrip("\n")
