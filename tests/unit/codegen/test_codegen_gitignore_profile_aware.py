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
        for marker in _WORKSPACE_ONLY_MARKERS:
            owners = tuple(
                section
                for section in config.Infra.codegen.gitignore_sections
                if marker in section.patterns
            )
            tm.that(owners, len=1)
            tm.that(owners[0].profiles, eq=(c.Infra.MakeProfile.WORKSPACE_ROOT,))
        rendered = _render_gitignore(tmp_path, c.Infra.MakeProfile.WORKSPACE_MEMBER)
        for marker in _WORKSPACE_ONLY_MARKERS:
            tm.that(
                rendered.splitlines(), lacks=marker, msg=f"phantom {marker} in member"
            )

    def test_workspace_root_gitignore_keeps_member_allowlist(
        self, tmp_path: Path
    ) -> None:
        """The workspace-root .gitignore keeps the member-directory allowlist."""
        rendered = _render_gitignore(tmp_path, c.Infra.MakeProfile.WORKSPACE_ROOT)
        for marker in _WORKSPACE_ONLY_MARKERS:
            tm.that(rendered.splitlines(), has=marker, msg=f"missing {marker} at root")


def _render_gitignore(tmp_path: Path, profile: c.Infra.MakeProfile) -> str:
    provider = config.Infra.codegen.providers[0]
    repository = m.Infra.RepositoryRef(
        name="fixture-project",
        distribution="fixture-project",
        url=f"{provider.base_url}/fixture-project.git",
        branch=provider.branch,
        path=Path(),
        role=c.Infra.RepositoryRole(profile.value),
        provider=provider.name,
        profile=profile,
        checkout=c.Infra.CheckoutKind.ROOT,
        codegen=c.Infra.CodegenKind.CONFORM,
        package=True,
        editable=True,
        read_only=False,
    )
    root = tmp_path / profile.value / repository.name
    workspace_root = (
        root.parent if profile is c.Infra.MakeProfile.WORKSPACE_MEMBER else root
    )
    workspace = m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name=repository.name,
        repository=repository,
        project=m.Infra.ProjectSpec(
            package_name="fixture_project",
            class_stem="FixtureProject",
            namespace="FixtureProject",
            constant_name=repository.name,
            namespace_attribute="fixture_project",
            alias="fixture_project",
            environment_prefix="FIXTURE_PROJECT_",
            description="Fixture project",
            version="0.12.0",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            homepage=f"{provider.base_url}/fixture-project",
            documentation=f"{provider.base_url}/fixture-project",
            workspace_root_rel=(
                ".." if profile is c.Infra.MakeProfile.WORKSPACE_MEMBER else "."
            ),
            year=2026,
        ),
        members=(),
    )
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
    tm.that(plan.repositories, len=1)
    tm.that(plan.repositories[0].profile, eq=profile)
    gitignore_plans = tuple(
        fp for fp in plan.files if Path(fp.path).name == c.Infra.GITIGNORE
    )
    tm.that(gitignore_plans, len=1)
    rendered: str = gitignore_plans[0].rendered
    return rendered


__all__: tuple[str, ...] = ()
