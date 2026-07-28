"""Generated .gitignore is profile-aware: no workspace-root phantom in members.

A workspace-member or standalone project has no ``flext-*/`` member directories
and no ``config/workspace.yaml``; emitting those allowlist patterns into their
``.gitignore`` is a phantom entry. The conform render must filter gitignore
sections by the repository profile so the workspace-root-only section only
appears in the workspace-root ``.gitignore``.
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm

_WORKSPACE_ONLY_MARKERS = ("!flext-*/", "!/config/workspace.yaml", "!flext-*/**")


class TestsCodegenGitignoreProfileAware:
    def test_member_gitignore_has_no_workspace_root_phantom(
        self, tmp_path: Path
    ) -> None:
        """A member .gitignore excludes workspace-root-only allowlist patterns."""
        project_root, workspace = _fixture_workspace(
            tmp_path, c.Infra.RepositoryRole.WORKSPACE_MEMBER
        )
        rendered = _render_gitignore(
            project_root, workspace_root=project_root, workspace=workspace
        )
        for marker in _WORKSPACE_ONLY_MARKERS:
            tm.that(marker not in rendered, eq=True, msg=f"phantom {marker} in member")

    def test_workspace_root_gitignore_keeps_member_allowlist(
        self, tmp_path: Path
    ) -> None:
        """The workspace-root .gitignore keeps the member-directory allowlist."""
        workspace_root, workspace = _fixture_workspace(
            tmp_path, c.Infra.RepositoryRole.WORKSPACE_ROOT
        )
        rendered = _render_gitignore(
            workspace_root, workspace_root=workspace_root, workspace=workspace
        )
        for marker in _WORKSPACE_ONLY_MARKERS:
            tm.that(marker in rendered, eq=True, msg=f"missing {marker} at root")


def _fixture_workspace(
    tmp_path: Path, role: c.Infra.RepositoryRole
) -> tuple[Path, m.Infra.WorkspaceSpec]:
    provider = config.Infra.codegen.providers[0]
    repository = (
        next(
            repository
            for repository in config.Infra.codegen.repositories
            if repository.role is c.Infra.RepositoryRole.WORKSPACE_ROOT
        ).model_copy(update={"path": Path()})
        if role is c.Infra.RepositoryRole.WORKSPACE_ROOT
        else m.Infra.RepositoryRef(
            name="fixture-member",
            distribution="fixture-member",
            provider=provider.name,
            url=f"{provider.base_url}/fixture-member.git",
            branch=provider.branch,
            path=Path(),
            role=role,
            state=c.Infra.RepositoryState.ACTIVE,
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
            checkout=c.Infra.CheckoutKind.ROOT,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=True,
            read_only=False,
        )
    )
    project_root = tmp_path / role.value / repository.name
    project_root.mkdir(parents=True)
    workspace = m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name=repository.name,
        repository=repository,
        project=m.Infra.ProjectSpec(
            package_name=repository.distribution.replace("-", "_"),
            class_stem="FixtureRoot",
            namespace="FixtureRoot",
            constant_name=repository.name,
            namespace_attribute="fixture_root",
            alias="fixture_root",
            environment_prefix="FIXTURE_ROOT_",
            description="Profile-aware gitignore fixture",
            version="0.12.0",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            homepage=repository.url.removesuffix(".git"),
            documentation=repository.url.removesuffix(".git"),
            workspace_root_rel=(
                ".." if role is c.Infra.RepositoryRole.WORKSPACE_MEMBER else "."
            ),
            year=2026,
        ),
    )
    return project_root, workspace


def _render_gitignore(
    root: Path, *, workspace_root: Path, workspace: m.Infra.WorkspaceSpec
) -> str:
    request = m.Infra.CodegenConformRequest(
        root=root,
        what=c.Infra.CodegenConformSurface.ALL,
        scope=c.Infra.CodegenConformScope.SELF,
        mode=c.Infra.CodegenConformMode.CHECK,
    )
    plan = (
        FlextInfraCodegenConform(
            workspace_root=workspace_root, request=request, initial_workspace=workspace
        )
        .plan(request)
        .unwrap()
    )
    gitignore_plans = tuple(
        fp for fp in plan.files if Path(fp.path).name == c.Infra.GITIGNORE
    )
    tm.that(gitignore_plans, len=1)
    rendered: str = gitignore_plans[0].rendered
    return rendered


__all__: tuple[str, ...] = ()
