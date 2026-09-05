"""Repository-local codegen extension contracts."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from flext_tests import tm
from tests import u as test_u
from tests.unit.workspace import WorktreeFixture

pytestmark = pytest.mark.slow


def _repository(
    name: str, *, path: str, role: c.Infra.MakeProfile
) -> m.Infra.RepositoryRef:
    reference = test_u.Tests.repository_ref(name, path=Path(path), role=role)
    is_standalone = role is c.Infra.MakeProfile.STANDALONE
    return reference.model_copy(
        update={"package": is_standalone, "editable": is_standalone}
    )


class TestsCodegenCatalogExtensions:
    """Prove generic extensions without a repository registry or second manifest."""

    def test_infra_repository_identity_is_owned_by_codegen_config(self) -> None:
        codegen = config.Infra.codegen
        source = codegen.infra_repository
        resolved = tm.ok(u.Infra.configured_repository_ref(codegen=codegen))

        tm.that(resolved.distribution, eq=source.distribution)
        tm.that(resolved.provider, eq=source.provider)
        tm.that(source.internal_distribution_prefix, eq="flext-")

    def test_infra_repository_provider_must_resolve_exactly_once(self) -> None:
        codegen = config.Infra.codegen
        source = codegen.infra_repository
        provider = next(
            item for item in codegen.providers if item.name == source.provider
        )
        unknown = codegen.model_copy(
            update={
                "infra_repository": source.model_copy(
                    update={"provider": "unknown-provider"}
                )
            }
        )
        duplicate = codegen.model_copy(
            update={"providers": (*codegen.providers, provider)}
        )

        unknown_result = u.Infra.configured_repository_ref(codegen=unknown)
        duplicate_result = u.Infra.configured_repository_ref(codegen=duplicate)

        tm.that(unknown_result.failure, eq=True)
        tm.that(unknown_result.error, has="must resolve exactly once")
        tm.that(duplicate_result.failure, eq=True)
        tm.that(duplicate_result.error, has="must resolve exactly once")

    def test_beads_toolchain_resolves_the_latest_fork_release(self) -> None:
        tm.that(config.Infra.codegen.toolchain.beads.version, eq="latest")

    def test_bootstrap_toolchain_pins_one_tracked_mise_release(self) -> None:
        """The tracked launchers are the pinned Mise owner, not a config floor.

        The toolchain SSOT declared ``mise_version`` until the Mise transaction
        made ``bin/mise``/``bin/mise.cmd`` the committed, checksum-verified
        owner. The live contract is therefore that both launchers embed exactly
        one valid release, which is what this asserts.
        """
        release = test_u.Tests.mise_release()

        tm.that(FlextInfraCodegenMiseArtifacts.is_mise_release(release), eq=True)

    def test_conform_has_no_global_workspace_catalog_validator(self) -> None:
        tm.that(
            hasattr(FlextInfraCodegenConform, "_validate_workspace_catalog"), eq=False
        )

    def test_codegen_composes_project_mise_tools_through_toml(
        self, tmp_path: Path
    ) -> None:
        """The codegen artifact boundary consumes the project YAML overlay."""
        python_version = config.Infra.codegen.toolchain.python_version
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "tooling.yaml").write_text(
            "ManagedArtifacts:\n  Mise:\n    tools:\n      node:\n        version: '26'\n",
            encoding="utf-8",
        )

        result = FlextInfraCodegenConform._compose_project_artifact(  # ruff: ignore[private-member-access]
            tmp_path,
            c.Infra.MISE_TOML_FILENAME,
            f'[tools]\npython = "{python_version}"\n',
        )

        rendered = tomllib.loads(tm.ok(result).rendered)
        tm.that(rendered["tools"], eq={"python": python_version, "node": "26"})

    def test_local_manifest_conforms_without_global_repository_rows(
        self, tmp_path: Path
    ) -> None:
        root = _repository(
            "acme-platform", path=".", role=c.Infra.MakeProfile.WORKSPACE
        )
        member = _repository(
            "acme-charts", path="acme-charts", role=c.Infra.MakeProfile.STANDALONE
        )
        workspace = m.Infra.WorkspaceSpec(
            name=root.name,
            beads=test_u.Tests.beads_project(root.name),
            repository=root,
            project=test_u.Tests.project_spec(root.name),
            declared_repositories=(member,),
        )
        provider = test_u.Tests.provider()
        member_source = tmp_path / "member-source"
        WorktreeFixture.initialize_governed_project(
            member_source,
            member.distribution,
            workspace=member.name,
            database=member.name,
            issue_prefix=member.name,
            beads_owner=False,
        )
        member_head = tm.ok(
            u.Cli.capture([c.Infra.GIT, "rev-parse", "HEAD"], cwd=member_source)
        )
        bare_repo = tmp_path / "acme-charts.git"
        tm.ok(
            u.Cli.run_checked([
                c.Infra.GIT,
                "clone",
                "--bare",
                member_source.as_posix(),
                bare_repo.as_posix(),
            ])
        )
        tm.ok(
            u.Cli.run_checked([
                c.Infra.GIT,
                "--git-dir",
                bare_repo.as_posix(),
                "update-ref",
                f"refs/heads/{provider.branch}",
                member_head,
            ])
        )

        repository_root = tmp_path / "workspace"
        WorktreeFixture.initialize_governed_project(
            repository_root,
            root.distribution,
            workspace=root.name,
            database=root.name,
            issue_prefix=root.name,
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    "-b",
                    provider.branch,
                    bare_repo.as_posix(),
                    member.name,
                ],
                cwd=repository_root,
            )
        )
        member_checkout = repository_root / member.name
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "remote", "set-url", "origin", member.url],
                cwd=member_checkout,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "config", "remote.origin.skipDefaultUpdate", "true"],
                cwd=member_checkout,
            )
        )
        WorktreeFixture.link_member_beads(
            member_checkout,
            repository_root,
            workspace_name=root.name,
            database=root.name,
            issue_prefix=root.name,
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "update-ref",
                    f"refs/remotes/origin/{provider.branch}",
                    member_head,
                ],
                cwd=member_checkout,
            )
        )
        gitmodules = WorktreeFixture.write_gitmodules(repository_root, (member.name,))
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "add", c.Infra.GITMODULES, member.name],
                cwd=repository_root,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "commit", "-q", "-m", "Attach governed member"],
                cwd=repository_root,
            )
        )
        root_head = tm.ok(
            u.Cli.capture([c.Infra.GIT, "rev-parse", "HEAD"], cwd=repository_root)
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "update-ref",
                    f"refs/remotes/origin/{provider.branch}",
                    root_head,
                ],
                cwd=repository_root,
            )
        )
        declared_gitmodules = gitmodules.read_bytes()

        result = FlextInfraCodegenConform(initial_workspace=workspace).plan(
            m.Infra.CodegenConformRequest(
                root=repository_root,
                what=c.Infra.CodegenConformSurface.ALL,
                scope=c.Infra.CodegenConformScope.ALL,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )

        plan = tm.ok(result)
        tm.that(
            tuple(item.name for item in plan.repositories), eq=(root.name, member.name)
        )
        root_makefile = next(
            file
            for file in plan.files
            if file.path == repository_root.resolve() / c.Infra.MAKEFILE_FILENAME
        )
        tm.that(root_makefile.rendered, has=f"DECLARED_REPOSITORIES := {member.name}")
        gitmodules_plan = next(
            file for file in plan.files if file.path == gitmodules.resolve()
        )
        tm.that(gitmodules_plan.policy, eq="manual")
        tm.that(gitmodules_plan.changed, eq=False)
        tm.that(gitmodules_plan.rendered.encode(), eq=declared_gitmodules)
        tm.that(gitmodules.read_bytes(), eq=declared_gitmodules)


__all__: tuple[str, ...] = ()
