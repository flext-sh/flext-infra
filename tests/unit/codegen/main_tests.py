"""Tests for the centralized codegen CLI group.

Validates CLI argument parsing, command dispatch, and exit codes
using real service instances with temporary workspaces.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import c, config
from flext_infra import main as infra_main
from flext_infra.services.cli_routes import CliRouteService
from flext_tests import tm
from tests import u

if TYPE_CHECKING:
    from tests import t


def _with_pep621_identity(repo: Path) -> Path:
    """Give the bare fixture repository the PEP 621 identity ``init`` derives from.

    The bootstrap projection reads declarations only: ``config/workspace.yaml``
    when present, otherwise the project name and its provider-matched
    Repository URL. A checkout with neither has no identity to render.
    """
    repository = u.Tests.repository_ref(repo.name)
    (repo / "pyproject.toml").write_text(
        f'[project]\nname = "{repository.distribution}"\nversion = "0.1.0"\n'
        'requires-python = ">=3.13,<3.14"\n\n'
        f'[project.urls]\nRepository = "{repository.url}"\n',
        encoding="utf-8",
    )
    return repo


class TestHandleLazyInit:
    """Tests for direct init command dispatch."""

    @staticmethod
    def _init(repo: Path, mode: str) -> int:
        """Run one bootstrap init through the public CLI entry point."""
        return infra_main([
            "codegen",
            "init",
            mode,
            "--workspace",
            str(_with_pep621_identity(repo)),
        ])

    def test_check_reports_drift_while_the_dispatcher_is_absent(
        self, real_git_repo: Path
    ) -> None:
        """A checkout without the generated dispatcher is drift, never clean.

        Check mode answers one question: does the checkout already carry the
        projection this generator would write? A bare repository does not, so
        reporting success there would let a stale or missing Makefile pass the
        gate that exists to catch exactly that.
        """
        tm.that(self._init(real_git_repo, "--check"), ne=0)

    def test_apply_bootstraps_the_dispatcher_to_a_fixed_point(
        self, real_git_repo: Path
    ) -> None:
        """Apply writes the dispatcher and a following check finds no drift."""
        tm.that(self._init(real_git_repo, "--apply"), eq=0)

        tm.that(self._init(real_git_repo, "--check"), eq=0)


class TestMainCommandDispatch:
    """Tests for main() command routing."""

    def test_unknown_command(self) -> None:
        """main() with unknown command returns non-zero exit code."""
        result = infra_main(["codegen", "unknown-command"])
        tm.that(result, ne=0)

    def test_no_command(self) -> None:
        """main() with no command returns non-zero exit code."""
        result = infra_main(["codegen"])
        tm.that(result, ne=0)

    def test_init_with_custom_root(self, real_git_repo: Path) -> None:
        """main() init with custom root directory."""
        custom_root = real_git_repo / "custom"
        custom_root.mkdir()
        result = infra_main([
            "codegen",
            "init",
            "--apply",
            "--workspace",
            str(_with_pep621_identity(custom_root)),
        ])
        tm.that(result, eq=0)


# Exemplar: every test here spawns a fresh interpreter to prove the real
# `python -m flext_infra` entry point. That import chain, not the assertion,
# dominates the runtime, so the class opts into the config-owned slow budget.
@pytest.mark.slow
class TestMainEntryPoint:
    """Tests for the centralized process entrypoint."""

    def test_entry_point_via_sys_exit(self) -> None:
        """The root process entrypoint serves each route's own declared help.

        The expectation is read from the route table that renders the help, so
        renaming or rewording a command keeps this contract honest instead of
        freezing yesterday's wording in the test.
        """
        route = next(
            item
            for item in CliRouteService.route_table_for(c.Infra.CLI_GROUP_CODEGEN)
            if item.name == "init"
        )

        result = u.Cli.run_raw([
            sys.executable,
            "-m",
            "flext_infra",
            c.Infra.CLI_GROUP_CODEGEN,
            route.name,
            "--help",
        ])

        tm.ok(result)
        tm.that(
            result.value.exit_code, eq=0, msg=result.value.stderr or result.value.stdout
        )
        tm.that(" ".join(result.value.stdout.split()), contains=route.help_text)

    def test_apply_bootstraps_managed_conflict_before_facade_imports(
        self, infra_git_repo: Path
    ) -> None:
        """Repair invalid target metadata through the real process entrypoint."""
        root = infra_git_repo
        project_root = Path(__file__).resolve().parents[3]
        tm.ok(
            u.Cli.files_copy_directory(
                project_root / "src" / "flext_infra",
                root / "src" / "flext_infra",
                dirs_exist_ok=True,
            )
        )
        tm.ok(
            u.Cli.files_copy_directory(
                project_root / "config", root / "config", dirs_exist_ok=True
            )
        )
        # The full surface validates the committed Mise seeds instead of minting
        # them, so the governed fixture carries them exactly as a repository does.
        u.Tests.copy_tracked_mise_seeds(root)
        (root / "pyproject.toml").write_text(
            '[project]\nname = "flext-infra"\nversion = "0.12.0.dev0"\n'
            'requires-python = ">=3.13,<3.14"\n'
            "\n"
            "[tool.pytest.ini_options]\n"
            "addopts = [\n"
            "<<<<<<< HEAD\n"
            '  "--timeout=90",\n'
            "=======\n"
            '  "--timeout=10",\n'
            ">>>>>>> origin/0.12.0-dev\n"
            "]\n",
            encoding="utf-8",
        )

        result = u.Cli.run_raw(
            [
                sys.executable,
                "-m",
                "flext_infra",
                "codegen",
                "conform",
                "--root",
                str(root),
                "--scope",
                "self",
                "--mode",
                "apply",
            ],
            cwd=root,
            env={"PYTHONPATH": str(root / "src")},
        )

        tm.ok(result)
        tm.that(
            result.value.exit_code, eq=0, msg=result.value.stderr or result.value.stdout
        )
        tm.that(
            result.value.stdout + result.value.stderr,
            contains="recovered owner-declared managed conflicts",
        )
        rendered = (root / "pyproject.toml").read_text(encoding="utf-8")
        tm.that(rendered, lacks="<<<<<<<")
        payload = tomllib.loads(rendered)
        tm.that(
            payload["tool"]["pytest"]["ini_options"]["addopts"],
            has=(f"--timeout={config.Infra.tooling.tools.pytest.case_timeout_seconds}"),
        )

    def test_unknown_command_surfaces_root_cause_via_subprocess(self) -> None:
        """Unknown codegen subcommands must print the actual CLI failure."""
        # The child renders through the CLI console, which honours COLUMNS and
        # would otherwise wrap the message at the developer's terminal width,
        # splitting the asserted phrase. Pin the width so the assertion tests
        # the message, not the terminal the suite happens to run in.
        result = u.Cli.run_raw(
            [sys.executable, "-m", "flext_infra", "codegen", "unknown-command"],
            env={"COLUMNS": "200"},
        )

        tm.ok(result)
        tm.that(result.value.exit_code, eq=2)
        tm.that(
            result.value.stdout + result.value.stderr,
            contains="No such command 'unknown-command'",
        )


__all__: t.StrSequence = []
