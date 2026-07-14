"""Public release CLI and model tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import main
from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
from tests import c
from tests import TestsFlextInfraUtilities as u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


def test_release_group_help_returns_zero() -> None:
    tm.that(main(["release", "--help"]), eq=0)


def test_release_run_subcommand_help_returns_zero() -> None:
    tm.that(main(["release", "run", "--help"]), eq=0)


def test_release_orchestrator_defaults_are_public_and_typed() -> None:
    params = FlextInfraReleaseOrchestrator.model_validate({})

    tm.that(list(params.phase_names), eq=list(c.Infra.ReleasePhase))
    tm.that(params.project_names, none=True)
    tm.that(params.push, eq=False)
    tm.that(params.next_bump, eq=c.Tests.RELEASE_BUMP_MINOR)


def test_release_orchestrator_normalizes_phase_and_projects() -> None:
    params = FlextInfraReleaseOrchestrator.model_validate({
        "phase": (f"{c.Tests.RELEASE_PHASE_VALIDATE} {c.Tests.RELEASE_PHASE_BUILD}"),
        "projects": ["flext-core", "flext-api"],
        "interactive": 0,
        "create_branches": 0,
    })

    tm.that(list(params.phase_names), eq=[c.Infra.VERB_VALIDATE, c.Infra.DIR_BUILD])
    tm.that(list(params.project_names or ()), eq=["flext-core", "flext-api"])
    tm.that(params.interactive, eq=0)
    tm.that(params.create_branches, eq=0)


def test_release_run_validate_dry_run_succeeds(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    result = main([
        "release",
        "run",
        "--workspace",
        str(workspace),
        "--phase",
        c.Tests.RELEASE_PHASE_VALIDATE,
        "--interactive",
        "0",
        "--dry-run",
    ])

    tm.that(result, eq=0)


def test_release_run_validate_apply_propagates_make_failure(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path, root_validate_exit_code="1")

    result = main([
        "release",
        "run",
        "--workspace",
        str(workspace),
        "--phase",
        c.Tests.RELEASE_PHASE_VALIDATE,
        "--interactive",
        "0",
        "--apply",
    ])

    tm.that(result, eq=1)
