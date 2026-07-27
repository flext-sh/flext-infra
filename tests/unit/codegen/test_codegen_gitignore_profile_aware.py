"""Generated .gitignore is profile-aware: no workspace-root phantom in members.

A workspace-member or standalone project has no ``flext-*/`` member directories
and no ``config/workspace.yaml``; emitting those allowlist patterns into their
``.gitignore`` is a phantom entry. The conform render must filter gitignore
sections by the repository profile so the workspace-root-only section only
appears in the workspace-root ``.gitignore``.
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import c, m
from flext_infra.codegen.conform import FlextInfraCodegenConform

_ROOT = Path(__file__).resolve().parents[3].parent
_WORKSPACE_ONLY_MARKERS = ("!flext-*/", "!/config/workspace.yaml", "!flext-*/**")


class TestsCodegenGitignoreProfileAware:
    def test_member_gitignore_has_no_workspace_root_phantom(self) -> None:
        """A member .gitignore excludes workspace-root-only allowlist patterns."""
        rendered = _render_gitignore(_ROOT / "flext-grpc")
        for marker in _WORKSPACE_ONLY_MARKERS:
            tm.that(marker not in rendered, eq=True, msg=f"phantom {marker} in member")

    def test_workspace_root_gitignore_keeps_member_allowlist(self) -> None:
        """The workspace-root .gitignore keeps the member-directory allowlist."""
        rendered = _render_gitignore(_ROOT)
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
