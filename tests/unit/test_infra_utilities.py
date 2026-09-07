"""Tests for u facade.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c
from flext_tests import tm
from tests import u


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

    def test_ast_grep_command_loads_utility_rules_from_owner_config(self) -> None:
        """Build scans through sgconfig so shared utility matches always resolve."""
        root = Path(__file__).parents[2]
        rule = (
            root
            / "src"
            / "flext_infra"
            / c.Infra.CODEMOD_RESOURCE_DIRNAME
            / c.Cli.RULES_DIR_NAME
            / "config-dict-type-from-typings.yml"
        )

        command = u.Infra.ast_grep_scan_command(rule)

        tm.that(command, has=c.Infra.SG_CONFIG_FLAG)
        tm.that(command, has=c.Infra.SG_FILTER_FLAG)
        tm.that(command, has="config-dict-type-from-typings")
        tm.that(command, lacks="--rule")
