"""Public module-entrypoint behavior tests.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest

from flext_infra import c
from flext_infra.cli import main


class TestsFlextInfraModuleEntrypoint:
    """Verify the public ``python -m flext_infra`` command surface."""

    def test_help_runs_without_reentering_the_package_root(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The module entrypoint delegates directly to its CLI implementation."""
        exit_code = main(("--help",))
        captured = capsys.readouterr()

        if exit_code != 0:
            pytest.fail(captured.err or captured.out)
        if "Usage: flext-infra <group>" not in captured.out:
            pytest.fail(f"unexpected module help: {captured.out!r}")

    def test_group_invocation_resolves_routes_without_private_attr_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Invoking a command group reaches route resolution, not a Pydantic private attr."""
        exit_code = main((c.Infra.CLI_GROUP_CHECK,))
        captured = capsys.readouterr()

        if exit_code != 1:
            pytest.fail(f"unexpected group help exit code: {exit_code}")
        combined = f"{captured.out}{captured.err}"
        if "is not subscriptable" in combined:
            pytest.fail(f"group route resolution crashed: {combined!r}")
        if "Traceback (most recent call last)" in captured.err:
            pytest.fail(captured.err)


__all__: tuple[str, ...] = ()
