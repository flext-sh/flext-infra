"""Generated .gitignore is profile-aware: no workspace-root phantom in members.

A workspace-member or standalone project has no ``flext-*/`` member directories
and no ``config/workspace.yaml``; emitting those allowlist patterns into their
``.gitignore`` is a phantom entry. The conform render must filter gitignore
sections by the repository profile so the workspace-root-only section only
appears in the workspace-root ``.gitignore``.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_infra import c, config, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import u as test_u

# Member allowlist patterns are DERIVED from the workspace manifest, so the
# expectation is built from the fixture's own members instead of freezing the
# glob the generator happens to emit today.
_WORKSPACE_ONLY_MARKERS = ("!/config/workspace.yaml",)


class TestsCodegenGitignoreProfileAware:
    def test_member_gitignore_has_no_workspace_root_phantom(self) -> None:
        """A member .gitignore excludes workspace-root-only allowlist patterns.

        The render seam is pure, so the profile is declared outright. Planning
        against the live checkout would read whatever topology this repository
        happens to have today and would race concurrent fixtures under xdist.
        """
        rendered = tm.ok(
            FlextInfraCodegenConform.render_project_gitignore(
                config.Infra.codegen,
                profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
                project_name="probe-member",
            )
        )
        for marker in _WORKSPACE_ONLY_MARKERS:
            tm.that(marker not in rendered, eq=True, msg=f"phantom {marker} in member")

    def test_workspace_root_gitignore_keeps_member_allowlist(self) -> None:
        """The workspace-root .gitignore keeps the member-directory allowlist.

        The render seam is pure: it takes the profile and the workspace topology
        and returns text. Materialising a real Git superproject with a real
        submodule proved nothing extra about that function, while making the
        test depend on live filesystem and Git state.
        """
        member = test_u.Tests.repository_ref(
            "probe-member",
            path=Path("probe-member"),
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
        )
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name="probe-root",
            repository=test_u.Tests.repository_ref("probe-root"),
            members=(member,),
        )

        rendered = tm.ok(
            FlextInfraCodegenConform.render_project_gitignore(
                config.Infra.codegen,
                profile=c.Infra.MakeProfile.WORKSPACE_ROOT,
                project_name="probe-root",
                workspace=workspace,
            )
        )

        for marker in _WORKSPACE_ONLY_MARKERS:
            tm.that(marker in rendered, eq=True, msg=f"missing {marker} at root")
        # The allowlist is derived from THIS fixture's declared member, so the
        # assertion follows any manifest instead of a frozen glob.
        member_path = member.path.as_posix()
        for marker in (f"!/{member_path}/", f"!/{member_path}/**"):
            tm.that(
                marker in rendered, eq=True, msg=f"missing derived {marker} at root"
            )

    def test_independent_overlay_projects_configured_mise_tool(
        self, tmp_path: Path
    ) -> None:
        """Derive the Mise tool selector and version from the typed owner."""
        repository, plan = _plan_independent_overlay(tmp_path)
        by_path = {
            file.path.relative_to(tmp_path / repository.name).as_posix(): file.rendered
            for file in plan.files
        }
        beads = config.Infra.codegen.toolchain.beads
        rendered_beads = tomllib.loads(by_path[".mise.toml"])["tools"][beads.selector]
        tm.that(rendered_beads["version"], eq=beads.version)
        tm.that(rendered_beads["prerelease"], eq=beads.prerelease)


def _plan_independent_overlay(
    tmp_path: Path,
) -> tuple[m.Infra.RepositoryRef, m.Infra.CodegenPlan]:
    provider = config.Infra.codegen.providers[0]
    name = "sample-project"
    repository = m.Infra.RepositoryRef(
        name=name,
        distribution=name,
        provider=provider.name,
        url=f"{provider.base_url}/{name}.git",
        path=Path(),
        role=c.Infra.RepositoryRole.STANDALONE,
        state=c.Infra.RepositoryState.ACTIVE,
        checkout=c.Infra.CheckoutKind.INDEPENDENT,
        codegen=c.Infra.CodegenKind.CONFORM,
        package=True,
        editable=False,
        read_only=False,
    )
    workspace = m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name=name,
        repository=repository,
        project=m.Infra.ProjectSpec(
            package_name=name.replace("-", "_"),
            class_stem="SampleProject",
            namespace="SampleProject",
            constant_name=name,
            namespace_attribute=name.replace("-", "_"),
            alias=name.replace("-", "_"),
            environment_prefix="SAMPLE_PROJECT_",
            description="Independent project fixture",
            version="0.1.0",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            homepage=f"{provider.base_url}/{name}",
            documentation=f"{provider.base_url}/{name}",
            workspace_root_rel=".",
            year=2026,
        ),
    )
    root = tmp_path / name
    request = m.Infra.CodegenConformRequest(
        root=root,
        scope=c.Infra.CodegenConformScope.SELF,
        mode=c.Infra.CodegenConformMode.CHECK,
    )
    plan: m.Infra.CodegenPlan = tm.ok(
        FlextInfraCodegenConform(
            workspace_root=root, request=request, initial_workspace=workspace
        ).plan(request)
    )
    return repository, plan


__all__: tuple[str, ...] = ()
