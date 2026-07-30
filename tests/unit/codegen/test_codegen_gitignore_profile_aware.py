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
_BEADS_CONFIG = "!.beads/config.yaml"


class TestsCodegenGitignoreProfileAware:
    def test_member_gitignore_has_no_workspace_root_phantom(self) -> None:
        """A member .gitignore excludes workspace-root-only allowlist patterns."""
        rendered = _render_gitignore(_ROOT)
        for marker in _WORKSPACE_ONLY_MARKERS:
            tm.that(marker not in rendered, eq=True, msg=f"phantom {marker} in member")
        tm.that(rendered, has=".beads/")
        tm.that(rendered, lacks=_BEADS_CONFIG)

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
        member_source = tmp_path / "member-source"
        member_source.mkdir()
        (member_source / "README.md").write_text(
            "fixture member\n", encoding=c.Cli.ENCODING_DEFAULT
        )
        test_u.Tests.initialize_git_repo(member_source)
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    "-q",
                    str(member_source),
                    member.path.as_posix(),
                ],
                cwd=root,
            )
        )
        rendered = _render_gitignore(root)
        for marker in _WORKSPACE_ONLY_MARKERS:
            tm.that(marker in rendered, eq=True, msg=f"missing {marker} at root")
        tm.that(rendered, has=_BEADS_CONFIG)

    def test_independent_overlay_generates_canonical_beads_environment(
        self, tmp_path: Path
    ) -> None:
        """Derive bd tool and project identity from typed production owners."""
        repository, plan = _plan_independent_overlay(tmp_path)
        by_path = {
            file.path.relative_to(tmp_path / repository.name).as_posix(): file.rendered
            for file in plan.files
        }
        beads_path = tmp_path / "rendered-beads-config.yaml"
        tm.ok(u.Cli.atomic_write_text_file(beads_path, by_path[".beads/config.yaml"]))
        beads_config = u.Cli.yaml_load_mapping(beads_path)
        tm.that(beads_config["issue-prefix"], eq=repository.name)
        dolt = u.Cli.json_as_mapping(beads_config["dolt"])
        tm.that(dolt["database"], eq=repository.name.replace("-", "_"))
        tm.that(
            by_path[".mise.toml"],
            has=(
                '"github:gastownhall/beads" = '
                f'"{config.Infra.codegen.toolchain.beads.version}"'
            ),
        )
        tm.that(by_path[c.Infra.GITIGNORE], has=_BEADS_CONFIG)


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
        branch=provider.branch,
        path=Path(),
        role=c.Infra.RepositoryRole.STANDALONE,
        state=c.Infra.RepositoryState.ACTIVE,
        profile=c.Infra.MakeProfile.STANDALONE,
        checkout=c.Infra.CheckoutKind.INDEPENDENT,
        codegen=c.Infra.CodegenKind.CONFORM,
        package=True,
        editable=False,
        read_only=False,
        beads=True,
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
