"""Repository-local codegen extension contracts."""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import WorktreeFixture, u as test_u


def _repository(
    name: str, *, path: str, role: c.Infra.RepositoryRole
) -> m.Infra.RepositoryRef:
    reference = test_u.Tests.repository_ref(name, path=Path(path), role=role)
    is_standalone = role is c.Infra.RepositoryRole.STANDALONE
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

    def test_beads_toolchain_uses_an_immutable_release_selector(self) -> None:
        selector = config.Infra.codegen.toolchain.beads.version

        version_parts = selector.split(".")
        is_semver = len(version_parts) == 3 and all(
            part.isdecimal() for part in version_parts
        )
        is_commit = len(selector) == 40 and all(
            char in "0123456789abcdef" for char in selector
        )
        tm.that(is_semver or is_commit, eq=True)

    def test_bootstrap_toolchain_uses_immutable_release_selectors(self) -> None:
        toolchain = config.Infra.codegen.toolchain

        mise_parts = toolchain.mise_version.split(".")
        tm.that(len(mise_parts), eq=3)
        tm.that(all(part.isdecimal() for part in mise_parts), eq=True)
        beads_version = toolchain.beads.version
        beads_parts = beads_version.split(".")
        beads_is_semver = len(beads_parts) == 3 and all(
            part.isdecimal() for part in beads_parts
        )
        beads_is_commit = len(beads_version) == 40 and all(
            char in "0123456789abcdef" for char in beads_version
        )
        tm.that(beads_is_semver or beads_is_commit, eq=True)

    def test_setup_provisions_only_and_gen_owns_conformance(self) -> None:
        """``make setup`` provisions tooling; ``make gen`` owns conformance."""
        template = (
            Path(__file__).parents[3]
            / "src"
            / "flext_infra"
            / "templates"
            / "project"
            / "base"
            / "Makefile.j2"
        )
        content = template.read_text(encoding="utf-8")
        tm.that("_builtin_setup_conform" in content, eq=False)
        setup_env = content.split("_builtin_setup_environment:", 1)[1]
        tm.that("codegen conform" in setup_env.split("\n\n", 1)[0], eq=False)
        tm.that("_builtin_gen_check:" in content, eq=True)
        tm.that("_builtin_gen_apply:" in content, eq=True)
        verb_names = {verb.name for verb in config.Infra.codegen.make.verbs}
        tm.that("conform" in verb_names, eq=False)

    def test_conform_has_no_global_workspace_catalog_validator(self) -> None:
        tm.that(
            hasattr(FlextInfraCodegenConform, "_validate_workspace_catalog"), eq=False
        )

    def test_codegen_composes_project_mise_tools_through_toml(
        self, tmp_path: Path
    ) -> None:
        """The codegen artifact boundary consumes the project YAML overlay."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "tooling.yaml").write_text(
            "ManagedArtifacts:\n  Mise:\n    tools:\n      node: '26'\n",
            encoding="utf-8",
        )

        result = FlextInfraCodegenConform._compose_project_artifact(  # ruff: ignore[private-member-access]
            tmp_path, c.Infra.MISE_TOML_FILENAME, '[tools]\npython = "3.13"\n'
        )

        rendered = tomllib.loads(tm.ok(result))
        tm.that(rendered["tools"], eq={"python": "3.13", "node": "26"})

    def test_local_manifest_conforms_without_global_repository_rows(
        self, tmp_path: Path
    ) -> None:
        root = _repository(
            "acme-platform", path=".", role=c.Infra.RepositoryRole.WORKSPACE
        )
        member = _repository(
            "acme-charts", path="acme-charts", role=c.Infra.RepositoryRole.STANDALONE
        )
        workspace = m.Infra.WorkspaceSpec(
            name=root.name,
            beads=test_u.Tests.beads_project(root.name),
            repository=root,
            project=test_u.Tests.project_spec(root.name),
            subprojects=(member,),
        )
        provider = test_u.Tests.provider()
        member_source = tmp_path / "member-source"
        WorktreeFixture.initialize_governed_project(
            member_source,
            member.distribution,
            workspace=member.name,
            database=member.name,
            issue_prefix=member.name,
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

        workspace_root = tmp_path / "workspace"
        WorktreeFixture.initialize_governed_project(
            workspace_root,
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
                cwd=workspace_root,
            )
        )
        member_checkout = workspace_root / member.name
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
        gitmodules = WorktreeFixture.write_gitmodules(workspace_root, (member.name,))
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "add", c.Infra.GITMODULES, member.name],
                cwd=workspace_root,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "commit", "-q", "-m", "Attach governed member"],
                cwd=workspace_root,
            )
        )
        root_head = tm.ok(
            u.Cli.capture([c.Infra.GIT, "rev-parse", "HEAD"], cwd=workspace_root)
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "update-ref",
                    f"refs/remotes/origin/{provider.branch}",
                    root_head,
                ],
                cwd=workspace_root,
            )
        )
        declared_gitmodules = gitmodules.read_bytes()

        result = FlextInfraCodegenConform(initial_workspace=workspace).plan(
            m.Infra.CodegenConformRequest(
                root=workspace_root,
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
            if file.path == workspace_root.resolve() / c.Infra.MAKEFILE_FILENAME
        )
        tm.that(root_makefile.rendered, has=f"WORKSPACE_SUBPROJECTS := {member.name}")
        tm.that(
            any(file.path.name == c.Infra.GITMODULES for file in plan.files), eq=False
        )
        tm.that(gitmodules.read_bytes(), eq=declared_gitmodules)


__all__: tuple[str, ...] = ()
