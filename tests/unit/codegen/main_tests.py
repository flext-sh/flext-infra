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

from flext_infra import CliRouteService, c, config, main as infra_main
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


def _seed_public_conform_checkout(root: Path) -> None:
    """Copy the real public package, config, and tracked Mise inputs into a repo."""
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
    u.Tests.copy_tracked_mise_seeds(root)
    tm.ok(
        u.Cli.files_copy(
            project_root / c.Infra.MISE_TOML_FILENAME, root / c.Infra.MISE_TOML_FILENAME
        )
    )


def _mise_transaction_state(root: Path) -> tuple[Path, Path]:
    """Return the public workspace journal and root-project staging paths."""
    toolchain = config.Infra.codegen.toolchain
    state_root = (
        root.parent
        / toolchain.state_directory_name
        / root.name
        / toolchain.mise_namespace
    )
    return state_root / "journal.json", state_root / "projects" / "root" / "transaction"


def _public_conform_command(root: Path) -> list[str]:
    """Build the real CLI command whose final argument selects check or apply."""
    return [
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
    ]


class TestHandleLazyInit:
    """Tests for direct init command dispatch."""

    def test_success(self, real_git_repo: Path) -> None:
        """Init returns 0 on empty workspace."""
        result = infra_main([
            "codegen",
            "init",
            "--apply",
            "--workspace",
            str(_with_pep621_identity(real_git_repo)),
        ])
        tm.that(result, eq=0)

    def test_check_mode(self, real_git_repo: Path) -> None:
        """Init check reports managed drift without mutating the repository."""
        repository = _with_pep621_identity(real_git_repo)
        pyproject = repository / c.Infra.PYPROJECT_FILENAME
        before = pyproject.read_bytes()
        makefile = repository / c.Infra.MAKEFILE_FILENAME
        result = infra_main([
            "codegen",
            "init",
            "--check",
            "--workspace",
            str(repository),
        ])
        tm.that(result, ne=0)
        tm.that(makefile.exists(), eq=False)
        tm.that(pyproject.read_bytes(), eq=before)

    def test_enforce_mode(self, real_git_repo: Path) -> None:
        """Init in enforce mode (not check)."""
        result = infra_main([
            "codegen",
            "init",
            "--apply",
            "--workspace",
            str(_with_pep621_identity(real_git_repo)),
        ])
        tm.that(result, eq=0)


class TestMainCommandDispatch:
    """Tests for main() command routing."""

    def test_init_command(self, real_git_repo: Path) -> None:
        """main() with init command returns 0."""
        result = infra_main([
            "codegen",
            "init",
            "--apply",
            "--workspace",
            str(_with_pep621_identity(real_git_repo)),
        ])
        tm.that(result, eq=0)

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

    def test_entry_point_returns_int(self, real_git_repo: Path) -> None:
        """main() returns an integer exit code."""
        result = infra_main([
            "codegen",
            "init",
            "--apply",
            "--workspace",
            str(_with_pep621_identity(real_git_repo)),
        ])
        tm.that(type(result).__name__, eq="int")

    def test_entry_point_via_sys_exit(self) -> None:
        """The root process entrypoint serves the route owner's declared help."""
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

    def test_managed_conflict_is_planned_and_published_atomically(
        self, infra_git_repo: Path
    ) -> None:
        """Keep live bytes unchanged until the public transaction commits."""
        root = infra_git_repo
        _seed_public_conform_checkout(root)
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

        pyproject = root / "pyproject.toml"
        before = pyproject.read_bytes()
        journal, transaction = _mise_transaction_state(root)
        command = _public_conform_command(root)
        checked = u.Cli.run_raw(
            [*command, "check"], cwd=root, env={"PYTHONPATH": str(root / "src")}
        )
        tm.ok(checked)
        tm.that(checked.value.exit_code, eq=1)
        tm.that(pyproject.read_bytes(), eq=before)
        tm.that(journal.exists(), eq=False)
        tm.that(transaction.exists(), eq=False)

        applied = u.Cli.run_raw(
            [*command, "apply"], cwd=root, env={"PYTHONPATH": str(root / "src")}
        )
        tm.ok(applied)
        tm.that(
            applied.value.exit_code,
            eq=0,
            msg=applied.value.stderr or applied.value.stdout,
        )
        rendered = pyproject.read_text(encoding="utf-8")
        tm.that(rendered, lacks="<<<<<<<")
        payload = tomllib.loads(rendered)
        tm.that(
            payload["tool"]["pytest"]["ini_options"]["addopts"],
            has=(f"--timeout={config.Infra.tooling.tools.pytest.case_timeout_seconds}"),
        )
        tm.that(journal.exists(), eq=False)
        tm.that(transaction.exists(), eq=False)

        published = pyproject.read_bytes()
        fixed_point = u.Cli.run_raw(
            [*command, "apply"], cwd=root, env={"PYTHONPATH": str(root / "src")}
        )
        tm.ok(fixed_point)
        tm.that(
            fixed_point.value.exit_code,
            eq=0,
            msg=fixed_point.value.stderr or fixed_point.value.stdout,
        )
        tm.that(pyproject.read_bytes(), eq=published)
        tm.that(journal.exists(), eq=False)
        tm.that(transaction.exists(), eq=False)

    def test_present_invalid_mise_artifact_never_enters_external_resolution(
        self, infra_git_repo: Path
    ) -> None:
        """Reject a present invalid artifact before credential/network work."""
        root = infra_git_repo
        _seed_public_conform_checkout(root)
        lock = root / "mise.lock"
        lock_state = tm.ok(u.Cli.atomic_read_binary_file_state(lock, required=True))
        lock_mode = lock_state.mode
        tm.that(lock_mode is None, eq=False)
        if lock_mode is None:
            msg = "required Mise lock has no permission mode"
            raise AssertionError(msg)
        if lock_state.content is None:
            msg = "required Mise lock has no bytes"
            raise AssertionError(msg)
        corrupted = lock_state.content + b"\ninvalid = [\n"
        tm.ok(
            u.Cli.atomic_write_binary_file_guarded(
                lock_state, corrupted, permission_mode=lock_mode
            )
        )
        journal, transaction = _mise_transaction_state(root)

        applied = u.Cli.run_raw(
            [*_public_conform_command(root), "apply"],
            cwd=root,
            env={"MISE_GITHUB_CREDENTIAL_COMMAND": "", "PYTHONPATH": str(root / "src")},
        )

        tm.ok(applied)
        tm.that(applied.value.exit_code, eq=1)
        tm.that(
            applied.value.stdout + applied.value.stderr,
            lacks="MISE_GITHUB_CREDENTIAL_COMMAND is required",
        )
        tm.that(lock.read_bytes(), eq=corrupted)
        tm.that(journal.exists(), eq=False)
        tm.that(transaction.exists(), eq=False)

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
