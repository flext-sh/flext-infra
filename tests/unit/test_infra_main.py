"""Tests for the centralized flext_infra CLI entrypoint.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest

from flext_infra import main


class TestsFlextInfraInfraMain:
    """Behavior contract for test_infra_main."""

    def test_main_returns_error_when_no_args(self) -> None:
        assert main([]) == 1

    def test_main_help_flag_returns_zero(self) -> None:
        assert main(["--help"]) == 0

    def test_main_unknown_group_returns_error(self) -> None:
        assert main(["unknown"]) == 1

    def test_main_help_lists_core_groups(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert main(["--help"]) == 0
        out = capsys.readouterr().out
        for group in ("basemk", "check", "codegen", "docs", "refactor", "workspace"):
            assert group in out
