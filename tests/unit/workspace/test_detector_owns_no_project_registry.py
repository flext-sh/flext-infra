"""Topology comes from the project, never from a registry inside flext-infra.

Operator law: flext-infra owns generic conform behaviour only. It must not
carry a registry of the projects it serves, so a repository's identity and its
projects are derived from that repository's own ``.gitmodules`` and local
``config/*.yaml`` overrides, and from nothing else.

A standalone repository derives its identity from its own ``pyproject.toml``
metadata and never consults a parent repository.
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm
from tests import u as test_u


def _standalone(root: Path, *, name: str) -> Path:
    """Create a real Git repository that flext-infra has never heard of."""
    (root / "src" / name.replace("-", "_")).mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        f"[project]\nname = '{name}'\nversion = '0.1.0'\n"
        "requires-python = '>=3.13,<3.14'\n",
        encoding="utf-8",
    )
    (root / "config").mkdir()
    (root / "config" / "beads.yaml").write_text(
        "version: 1\nworkspace: flext\ndatabase: flext\nissue_prefix: flext\n",
        encoding="utf-8",
    )
    test_u.Tests.initialize_git_repo(root)
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

    def test_only_own_gitmodules_changes_repository_mode(self, tmp_path: Path) -> None:
        """A parent .gitmodules never changes a standalone classification."""
        parent = tmp_path / "parent"
        parent.mkdir()
        (parent / ".gitmodules").write_text(
            '[submodule "child"]\n\tpath = child\n\turl = ../child.git\n',
            encoding="utf-8",
        )
        child = _standalone(parent / "child", name="child")

        mode = tm.ok(FlextInfraWorkspaceDetector().detect(child))

        tm.that(mode, eq=c.Infra.WorkspaceMode.STANDALONE)
