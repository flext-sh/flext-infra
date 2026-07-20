"""Public module-entrypoint behavior tests.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, u


class TestsFlextInfraModuleEntrypoint:
    """Verify the public ``python -m flext_infra`` command surface."""

    def test_help_runs_without_reentering_the_package_root(self) -> None:
        """The module entrypoint delegates directly to its CLI implementation."""
        project_root = Path(__file__).parents[2]

        completed = u.Cli.run_raw(
            (c.Infra.PYTHON, "-m", "flext_infra", "--help"), cwd=project_root
        ).unwrap()

        if completed.exit_code != 0:
            pytest.fail(completed.stderr or completed.stdout)
        if "Usage: flext-infra <group>" not in completed.stdout:
            pytest.fail(f"unexpected module help: {completed.stdout!r}")

    def test_group_invocation_resolves_routes_without_private_attr_error(self) -> None:
        """Invoking a command group reaches route resolution, not a Pydantic private attr."""
        project_root = Path(__file__).parents[2]

        completed = u.Cli.run_raw(
            (c.Infra.PYTHON, "-m", "flext_infra", c.Infra.CLI_GROUP_CHECK),
            cwd=project_root,
        ).unwrap()

        combined = f"{completed.stdout}{completed.stderr}"
        if "is not subscriptable" in combined:
            pytest.fail(f"group route resolution crashed: {combined!r}")
        if "Traceback (most recent call last)" in completed.stderr:
            pytest.fail(completed.stderr)


__all__: tuple[str, ...] = ()
