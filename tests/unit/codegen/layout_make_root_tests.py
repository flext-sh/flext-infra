"""Regression tests for checkout-derived REPOSITORY_ROOT in the flext-infra Makefile.

Guards the root-cause fix for the env-leak defect: an inherited
``REPOSITORY_ROOT`` from a foreign checkout (e.g. a leaked ``.envrc`` export)
must never redirect make verbs to another working tree (flext-hzox).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from flext_tests import tm

from tests import u


class TestsFlextInfraCodegenLayoutMakeRoot:
    """Test suite for checkout-derived REPOSITORY_ROOT resolution."""

    _REPO_ROOT = Path(__file__).resolve().parents[3]
    _MAKE = shutil.which("make") or "make"
    _GIT = shutil.which("git") or "git"

    def _git_root(self, *args: str) -> str:
        """Resolve a git root marker for the repository under test."""
        result = u.Cli.run_raw([
            self._GIT,
            "-C",
            str(self._REPO_ROOT),
            "rev-parse",
            *args,
        ])
        return result.value.stdout.strip() if result.success else ""

    def _make_database_repository_root(
        self, *extra_args: str, env: dict[str, str]
    ) -> str:
        """Read REPOSITORY_ROOT from the flext-infra make database."""
        result = u.Cli.run_raw(
            [self._MAKE, "-C", str(self._REPO_ROOT), "-pn", *extra_args], env=env
        )
        tm.ok(result)
        return next(
            line.split(" ", 2)[2].strip()
            for line in result.value.stdout.splitlines()
            if line.startswith(("REPOSITORY_ROOT =", "REPOSITORY_ROOT :="))
        )

    def test_make_repository_root_ignores_foreign_env_leak(
        self, tmp_path: Path
    ) -> None:
        """A poisoned environment REPOSITORY_ROOT never wins over the checkout."""
        env = dict(os.environ, REPOSITORY_ROOT=str(tmp_path / "foreign-checkout"))
        resolved = self._make_database_repository_root(env=env)
        expected = self._git_root("--show-superproject-working-tree") or self._git_root(
            "--show-toplevel"
        )
        tm.that(resolved, eq=expected)

    def test_make_repository_root_honors_command_line_override(
        self, tmp_path: Path
    ) -> None:
        """An explicit command-line REPOSITORY_ROOT stays authoritative."""
        override = str(tmp_path / "explicit-target")
        resolved = self._make_database_repository_root(
            f"REPOSITORY_ROOT={override}", env=dict(os.environ)
        )
        tm.that(resolved, eq=override)


__all__: list[str] = ["TestsFlextInfraCodegenLayoutMakeRoot"]
