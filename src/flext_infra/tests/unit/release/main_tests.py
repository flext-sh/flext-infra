"""Public release CLI and model tests."""

from __future__ import annotations

from pathlib import Path

from flext_infra import main
from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
from flext_infra.tests.constants import c
from tests.utilities import TestsFlextInfraUtilities as u


def test_release_group_help_returns_zero() -> None:
    assert main(["release", "--help"]) == 0


def test_release_run_subcommand_help_returns_zero() -> None:
    assert main(["release", "run", "--help"]) == 0


def test_release_orchestrator_defaults_are_public_and_typed() -> None:
    params = FlextInfraReleaseOrchestrator.model_validate({})

    assert list(params.phase_names) == list(c.Infra.ReleasePhase)
    assert params.project_names is None
    assert params.push is False
    assert params.next_bump == c.Tests.RELEASE_BUMP_MINOR


def test_release_orchestrator_normalizes_phase_and_projects() -> None:
    params = FlextInfraReleaseOrchestrator.model_validate(
        {
            "phase": (
                f"{c.Tests.RELEASE_PHASE_VALIDATE} {c.Tests.RELEASE_PHASE_BUILD}"
            ),
            "projects": ["flext-core", "flext-api"],
            "interactive": 0,
            "create_branches": 0,
        },
    )

    assert list(params.phase_names) == [
        c.Infra.VERB_VALIDATE,
        c.Infra.DIR_BUILD,
    ]
    assert list(params.project_names or ()) == ["flext-core", "flext-api"]
    assert params.interactive == 0
    assert params.create_branches == 0


def test_release_run_validate_dry_run_succeeds(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    result = main(
        [
            "release",
            "run",
            "--workspace",
            str(workspace),
            "--phase",
            c.Tests.RELEASE_PHASE_VALIDATE,
            "--interactive",
            "0",
            "--dry-run",
        ],
    )

    assert result == 0


def test_release_run_validate_apply_propagates_make_failure(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_release_workspace(
        tmp_path,
        root_validate_exit_code="1",
    )

    result = main(
        [
            "release",
            "run",
            "--workspace",
            str(workspace),
            "--phase",
            c.Tests.RELEASE_PHASE_VALIDATE,
            "--interactive",
            "0",
            "--apply",
        ],
    )

    assert result == 1
