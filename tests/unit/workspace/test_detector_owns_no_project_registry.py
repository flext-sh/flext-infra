"""Topology comes from the project, never from a registry inside flext-infra.

Operator law: flext-infra owns generic conform behaviour only. A repository's
identity and public-root contract come from its own ``pyproject.toml``. Its
topology is the independent presence-or-absence fact of its own ``.gitmodules``;
topology never creates project relationships or execution policy.
"""

from __future__ import annotations

from pathlib import Path

import pytest
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
    provider = config.Infra.codegen.providers[0]
    test_u.Tests.initialize_git_repo(
        root, f"{provider.base_url.rstrip('/')}/{name}.git"
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
        target = tm.ok(FlextInfraWorkspaceDetector.conform_target(root))

        tm.that(spec.repository.name, eq="totally-unknown")
        tm.that(spec.repository.path, eq=Path())
        tm.that("members" in type(spec).model_fields, eq=False)
        tm.that(target.managed, eq=False)

    def test_git_submodules_remain_the_topology_ssot(self, tmp_path: Path) -> None:
        """A .gitmodules file changes topology without creating member policy."""
        root = _standalone(tmp_path / "workspace-repo", name="workspace-repo")
        provider = config.Infra.codegen.providers[0]
        (root / ".gitmodules").write_text(
            f'[submodule "member-pkg"]\n\tpath = member-pkg\n\turl = https://github.com/{provider.name}/member-pkg.git\n\tbranch = {provider.branch}\n',
            encoding="utf-8",
        )
        _standalone(root / "member-pkg", name="member-pkg")

        mode = tm.ok(FlextInfraWorkspaceDetector().detect(root))
        spec = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(mode, eq=c.Infra.WorkspaceMode.WORKSPACE)
        tm.that("members" in type(spec).model_fields, eq=False)

    @pytest.mark.parametrize("workspace", [False, True])
    def test_empty_flext_table_declares_management_independently(
        self, tmp_path: Path, *, workspace: bool
    ) -> None:
        """An empty [tool.flext] table manages either repository topology."""
        root = _standalone(tmp_path / "managed-project", name="managed-project")
        pyproject = root / "pyproject.toml"
        pyproject.write_text(
            f"{pyproject.read_text(encoding='utf-8')}\n[tool.flext]\n", encoding="utf-8"
        )
        if workspace:
            (root / ".gitmodules").write_text("", encoding="utf-8")

        target = tm.ok(FlextInfraWorkspaceDetector.conform_target(root))

        tm.that(target.managed, eq=True)
        tm.that(
            target.topology,
            eq=(
                c.Infra.WorkspaceMode.WORKSPACE
                if workspace
                else c.Infra.WorkspaceMode.STANDALONE
            ),
        )
