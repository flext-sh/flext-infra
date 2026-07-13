"""Tests for u facade.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from tests import u
from flext_tests import tm


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

        block = u.Infra.extract_definition(source, "ExamplesFlextModels", kind="class")

        tm.that(u.Infra.bracket_balance_line("class ExamplesFlextModels("), eq=1)
        tm.that(block, eq=source.rstrip("\n"))
