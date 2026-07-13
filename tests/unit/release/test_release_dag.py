"""Public release orchestration tests using real workspaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
from tests.constants import c
from tests.models import m
from tests.utilities import u

if TYPE_CHECKING:
    from pathlib import Path

    from tests.typings import t


def _make_config(
    workspace_root: Path,
    *,
    phases: t.SequenceOf[str] | None = None,
    dry_run: bool = False,
) -> m.Infra.ReleaseOrchestratorConfig:
    return m.Infra.ReleaseOrchestratorConfig(
        workspace_root=workspace_root,
        version=c.Tests.RELEASE_VERSION_TARGET,
        tag=c.Tests.RELEASE_TAG_TARGET,
        phases=list(phases) if phases is not None else list(c.Tests.ALL_PHASES),
        project_names=None,
        dry_run=dry_run,
        push=False,
        dev_suffix=False,
        create_branches=False,
        next_dev=False,
        next_bump=c.Tests.RELEASE_BUMP_MINOR,
    )


class TestsFlextInfraReleaseDag:
    """Behavior contract for test_release_dag."""

    def test_release_succeed_in_dry_run_mode(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = u.Tests.create_release_workspace(
            tmp_path,
            project_names=("flext-a",),
        )
        result = FlextInfraReleaseOrchestrator().run_release(
            _make_config(workspace, dry_run=True),
        )

        assert result.success
        report_dir = workspace / ".reports" / "release" / c.Tests.RELEASE_TAG_TARGET
        assert (report_dir / "build-report.json").is_file()
        assert (report_dir / c.Tests.RELEASE_NOTES_FILENAME).is_file()

    def test_release_selected_validate_phase_skips_release_artifacts(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = u.Tests.create_release_workspace(tmp_path)
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
        workspace = u.Tests.create_release_workspace(
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
