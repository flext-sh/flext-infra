"""Public release orchestration tests using real workspaces."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraReleaseOrchestrator
from tests import c, m, u

_ALL_PHASES: list[str] = [
    c.Infra.VERB_VALIDATE,
    c.Infra.VERSION,
    c.Infra.DIR_BUILD,
    c.Infra.VERB_PUBLISH,
]


def _make_config(
    workspace_root: Path,
    *,
    phases: list[str] | None = None,
    dry_run: bool = False,
) -> m.Infra.ReleaseOrchestratorConfig:
    return m.Infra.ReleaseOrchestratorConfig(
        workspace_root=workspace_root,
        version="1.0.0",
        tag="v1.0.0",
        phases=phases or _ALL_PHASES,
        project_names=None,
        dry_run=dry_run,
        push=False,
        dev_suffix=False,
        create_branches=False,
        next_dev=False,
        next_bump="minor",
    )


class TestsFlextInfraReleaseDag:
    """Behavior contract for test_release_dag."""

    def test_release_all_phases_succeed_in_dry_run_mode(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = u.Infra.Tests.create_release_workspace(
            tmp_path,
            project_names=("flext-a",),
        )
        result = FlextInfraReleaseOrchestrator().run_release(
            _make_config(workspace, dry_run=True),
        )

        assert result.success
        report_dir = workspace / ".reports/release/v1.0.0"
        assert (report_dir / "build-report.json").is_file()
        assert (report_dir / "RELEASE_NOTES.md").is_file()

    def test_release_selected_validate_phase_skips_release_artifacts(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = u.Infra.Tests.create_release_workspace(tmp_path)
        result = FlextInfraReleaseOrchestrator().run_release(
            _make_config(
                workspace,
                phases=[c.Infra.VERB_VALIDATE],
                dry_run=True,
            ),
        )

        assert result.success
        assert not (workspace / ".reports/release").exists()

    def test_release_build_failure_propagates_from_real_make(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = u.Infra.Tests.create_release_workspace(
            tmp_path,
            root_build_exit_code="1",
        )
        result = FlextInfraReleaseOrchestrator().run_release(
            _make_config(
                workspace,
                phases=[c.Infra.DIR_BUILD],
                dry_run=False,
            ),
        )

        assert result.failure
        assert "build failed" in (result.error or "")
