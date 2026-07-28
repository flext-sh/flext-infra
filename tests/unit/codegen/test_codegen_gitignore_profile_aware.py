"""Generated .gitignore is profile-aware: no workspace-root phantom in members.

A workspace-member or standalone project has no ``flext-*/`` member directories
and no ``config/workspace.yaml``; emitting those allowlist patterns into their
``.gitignore`` is a phantom entry. The conform render must filter gitignore
sections by the repository profile so the workspace-root-only section only
appears in the workspace-root ``.gitignore``.
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import u as test_u

_ROOT = Path(__file__).resolve().parents[3]
_WORKSPACE_ONLY_MARKERS = ("!flext-*/", "!/config/workspace.yaml", "!flext-*/**")


class TestsCodegenGitignoreProfileAware:
    def test_member_gitignore_has_no_workspace_root_phantom(self) -> None:
        """A member .gitignore excludes workspace-root-only allowlist patterns."""
        rendered = _render_gitignore(_ROOT)
        for marker in _WORKSPACE_ONLY_MARKERS:
            tm.that(marker not in rendered, eq=True, msg=f"phantom {marker} in member")

    def test_workspace_root_gitignore_keeps_member_allowlist(
        self, tmp_path: Path
    ) -> None:
        """The workspace-root .gitignore keeps the member-directory allowlist."""
        root = tmp_path / "flext"
        root.mkdir()
        root_repository = next(
            repository
            for repository in config.Infra.codegen.repositories
            if repository.name == "flext"
        )
        member = next(
            repository
            for repository in config.Infra.codegen.repositories
            if repository.name == "flext-core"
        )
        (root / c.Infra.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'flext'\nversion = '0.12.0.dev0'\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=root_repository.name,
            repository=root_repository,
            members=(member,),
        )
        tm.ok(
            u.Cli.yaml_dump(
                root / "config" / c.Infra.WORKSPACE_MANIFEST_FILENAME,
                workspace.model_dump(mode="json", exclude_none=True),
            )
        )
        test_u.Tests.initialize_git_repo(root)
        rendered = _render_gitignore(root)
        for marker in _WORKSPACE_ONLY_MARKERS:
            tm.that(marker in rendered, eq=True, msg=f"missing {marker} at root")


def _render_gitignore(root: Path) -> str:
    plan = (
        FlextInfraCodegenConform()
        .plan(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.ALL,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
        .unwrap()
    )
    gitignore_plans = tuple(
        fp for fp in plan.files if Path(fp.path).name == c.Infra.GITIGNORE
    )
    tm.that(gitignore_plans, len=1)
    rendered: str = gitignore_plans[0].rendered
    return rendered


__all__: tuple[str, ...] = ()
