"""Tests for the centralized flext_infra CLI entrypoint.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from flext_infra import main
from flext_infra.cli_catalog import CliCatalog
from flext_tests import tm

if TYPE_CHECKING:
    import pytest


class TestsFlextInfraInfraMain:
    """Behavior contract for test_infra_main."""

    def test_main_returns_error_when_no_args(self) -> None:
        tm.that(main([]), eq=1)

    def test_main_help_flag_returns_zero(self) -> None:
        tm.that(main(["--help"]), eq=0)

    def test_main_unknown_group_returns_error(self) -> None:
        tm.that(main(["unknown"]), eq=1)

    def test_main_help_lists_core_groups(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        tm.that(main(["--help"]), eq=0)
        out = capsys.readouterr().out
        for group in ("basemk", "check", "codegen", "docs", "refactor", "workspace"):
            tm.that(out, has=group)

    def test_codegen_help_lists_lightweight_canonical_descriptors(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        tm.that(main(["codegen", "--help"]), eq=0)
        out = capsys.readouterr().out
        for name, description in CliCatalog.command_descriptions[
            "codegen"
        ].items():
            tm.that(out, has=name)
            tm.that(out, has=description)

    def test_codegen_unknown_command_is_usage_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        tm.that(main(["codegen", "missing-command"]), eq=2)
        tm.that(capsys.readouterr().out, has="unknown command 'missing-command'")

    def test_catalog_factory_keys_match_public_descriptors(self) -> None:
        tm.that(
            {
                group: tuple(commands)
                for group, commands in CliCatalog.factory_modules.items()
            },
            eq={
                group: tuple(commands)
                for group, commands in CliCatalog.command_descriptions.items()
            },
        )

    def test_all_group_help_avoids_every_implementation_factory(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        loaded_before = frozenset(sys.modules)
        for group, commands in CliCatalog.command_descriptions.items():
            tm.that(main([group, "--help"]), eq=0)
            output = capsys.readouterr().out
            for name, description in commands.items():
                tm.that(output, has=name)
                tm.that(output, has=description)
        newly_loaded = frozenset(sys.modules) - loaded_before
        implementation_modules = {
            module
            for commands in CliCatalog.factory_modules.values()
            for module in commands.values()
        }
        tm.that(newly_loaded.isdisjoint(implementation_modules), eq=True)

    def test_structural_selection_never_uses_an_option_value_as_command(self) -> None:
        tm.that(
            CliCatalog.selected_command(
                "codegen",
                ["--projects", "pipeline", "conform", "--what", "dependencies"],
            ),
            eq="conform",
        )
