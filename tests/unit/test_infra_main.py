"""Tests for the centralized flext_infra CLI entrypoint.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from flext_infra import c, main
from flext_infra.cli import FlextInfraCli
from flext_infra.services.cli_routes import CliRouteService
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
        for name, description in CliRouteService.command_descriptions(
            "codegen"
        ).items():
            tm.that(out, has=name)
            tm.that(out, has=description)

    def test_codegen_unknown_command_is_usage_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        tm.that(main(["codegen", "missing-command"]), eq=2)
        tm.that(capsys.readouterr().out, has="unknown command 'missing-command'")

    def test_every_public_group_has_selected_route_descriptors(self) -> None:
        for group in c.Infra.CLI_GROUP_DESCRIPTIONS:
            tm.that(CliRouteService.command_descriptions(group), where=bool)

    def test_all_group_help_avoids_heavy_command_implementations(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Probe representative heavy modules without owning the route catalog."""
        loaded_before = frozenset(sys.modules)
        for group in c.Infra.CLI_GROUP_DESCRIPTIONS:
            commands = CliRouteService.command_descriptions(group)
            tm.that(main([group, "--help"]), eq=0)
            output = capsys.readouterr().out
            for name, description in commands.items():
                tm.that(output, has=name)
                tm.that(output, has=description)
        newly_loaded = frozenset(sys.modules) - loaded_before
        tm.that(
            newly_loaded.isdisjoint({
                "flext_infra.codegen.pipeline",
                "flext_infra.release.orchestrator",
                "flext_infra.refactor.namespace_enforcer",
                "flext_infra.workspace.orchestrator",
            }),
            eq=True,
        )

    def test_structural_selection_never_uses_an_option_value_as_command(self) -> None:
        tm.that(
            FlextInfraCli.selected_command(
                "codegen",
                ["--projects", "pipeline", "conform", "--what", "dependencies"],
            ),
            eq="conform",
        )
