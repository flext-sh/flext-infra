"""Governed worktree transaction provenance tests.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import m, p, u


def _workspace(tmp_path: Path) -> Path:
    workspace_root = tmp_path / "workspace"
    consumer_package = workspace_root / "src" / "consumer_package"
    consumer_package.mkdir(parents=True)
    (consumer_package / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    shadow_package = workspace_root / "src" / "flext_infra"
    shadow_package.mkdir()
    (shadow_package / "__init__.py").write_text(
        'raise RuntimeError("consumer flext_infra shadow loaded")\n', encoding="utf-8"
    )
    (workspace_root / "pyproject.toml").write_text(
        '[project]\nname = "transaction-fixture"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    for command in (
        ("git", "init", "-q"),
        ("git", "config", "user.email", "tests@flext.sh"),
        ("git", "config", "user.name", "FLEXT Tests"),
        ("git", "add", "pyproject.toml", "src"),
        ("git", "commit", "-qm", "fixture"),
    ):
        result = u.Cli.run_raw(command, cwd=workspace_root)
        if result.failure or result.value.exit_code != 0:
            message = (
                result.error or result.value.stderr or "fixture Git command failed"
            )
            raise AssertionError(message)
    return workspace_root


def _execute(workspace_root: Path) -> p.Infra.WorktreeTransactionReport:
    result = u.Infra.execute_worktree_transaction(
        m.Infra.WorktreeTransactionRequest(
            workspace_root=workspace_root,
            command=(
                "deps",
                "modernize",
                "--workspace",
                str(workspace_root),
                "--dry-run",
                "--skip-check",
                "--output-format",
                "json",
            ),
            apply_patch=False,
            timeout_seconds=120,
        )
    )
    if result.failure:
        message = result.error or "governed transaction failed"
        raise AssertionError(message)
    return result.value


class TestsFlextInfraWorktreeTransaction:
    """Verify controller and consumer source provenance."""

    def test_public_transaction_uses_controller_code_and_config(
        self, tmp_path: Path
    ) -> None:
        """Reject a consumer shadow and emit the controller's tests-only Ruff policy."""
        report = _execute(_workspace(tmp_path))

        if report.command_output.exit_code != 0:
            pytest.fail(report.command_output.stderr)
        if "consumer flext_infra shadow loaded" in report.command_output.stderr:
            pytest.fail(report.command_output.stderr)
        expected_tokens = ("**/tests/**/*.py", "FBT001", "PLC1901", "S108")
        missing_tokens = tuple(
            token
            for token in expected_tokens
            if token not in report.command_output.stdout
        )
        if missing_tokens:
            pytest.fail(f"missing controller config tokens: {missing_tokens}")

    def test_public_transaction_keeps_consumer_packages_importable(
        self, tmp_path: Path
    ) -> None:
        """Import unrelated consumer packages after controller precedence is applied."""
        report = _execute(_workspace(tmp_path))

        if report.import_probe.exit_code != 0:
            pytest.fail(report.import_probe.stderr)
        if "imported 2 packages" not in report.import_probe.stdout:
            pytest.fail(report.import_probe.stdout)

    def test_ruff_command_normalizes_one_consumer_config(self) -> None:
        """Normalize absent, split, and joined Ruff config options deterministically."""
        consumer_config = Path("/isolated/pyproject.toml")
        commands = (
            ("ruff", "check", "."),
            ("ruff", "check", "--config", "other.toml", "."),
            ("ruff", "check", "--config=other.toml", "."),
        )

        for command in commands:
            normalized = u.Infra.normalize_ruff_lint_command(command, consumer_config)
            configs = tuple(
                argument
                for argument in normalized
                if argument == "--config" or argument.startswith("--config=")
            )
            if configs != (f"--config={consumer_config}",):
                pytest.fail(str(normalized))
