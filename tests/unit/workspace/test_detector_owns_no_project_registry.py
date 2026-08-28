"""Topology comes from each repository, never from an internal project registry."""

from __future__ import annotations

from pathlib import Path

from flext_infra import config
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm

from tests.unit.workspace.worktree_fixture import WorktreeFixture


def _standalone(root: Path, *, name: str) -> Path:
    """Create a real Git repository that flext-infra has never heard of."""
    WorktreeFixture.initialize_governed_project(
        root,
        name,
        workspace=f"{name}-workspace",
        database=f"{name}-database",
        issue_prefix=f"{name}-prefix",
    )
    return root


class TestsDetectorOwnsNoProjectRegistry:
    """Prove derivation never consults a flext-infra-owned project catalog."""

    def test_codegen_config_declares_no_project_registry(self) -> None:
        """flext-infra config carries generic policy, never a project list."""
        tm.that(
            hasattr(config.Infra.codegen, "repositories"),
            eq=False,
            msg="codegen config must not own a registry of served projects",
        )

    def test_unknown_project_derives_its_own_identity(self, tmp_path: Path) -> None:
        """A repository absent from any catalog still derives from itself."""
        root = _standalone(tmp_path / "totally-unknown-project", name="totally-unknown")

        spec = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(spec.name, eq="totally-unknown")
        tm.that(spec.repository.name, eq="totally-unknown")
        tm.that(spec.repository.path, eq=Path())
        tm.that(spec.subprojects, empty=True)
        tm.that(spec.beads.workspace, eq="totally-unknown-workspace")
