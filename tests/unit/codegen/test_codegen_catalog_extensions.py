"""Repository-local codegen extension contracts."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c, config, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from tests import u

pytestmark = pytest.mark.slow


class TestsFlextInfraCodegenCatalogExtensions:
    """Prove generic extensions without a repository registry or second manifest."""

    def _repository(
        self, name: str, *, path: str, role: c.Infra.MakeProfile
    ) -> m.Infra.RepositoryRef:
        reference = u.Tests.repository_ref(name, path=Path(path), role=role)
        is_standalone = role is c.Infra.MakeProfile.STANDALONE
        return reference.model_copy(
            update={"package": is_standalone, "editable": is_standalone}
        )

    def test_infra_repository_identity_is_detected_from_the_checkout(
        self, tmp_path: Path
    ) -> None:
        """The infra URL is detected from the checkout's own dependency line."""
        codegen = config.Infra.codegen
        source = codegen.infra_repository
        provider = u.Tests.provider()
        root = tmp_path / "infra-checkout"
        root.mkdir()
        (root / "pyproject.toml").write_text(
            '[project]\nname = "acme-platform"\nversion = "0.1.0"\n'
            "dependencies = []\n"
            "[dependency-groups]\n"
            f'codegen = ["flext-infra @ git+{provider.base_url}/flext-infra.git@'
            f'{u.Tests.provider_branch()}"]\n',
            encoding="utf-8",
        )

        resolved = tm.ok(
            u.Infra.configured_repository_ref(codegen=codegen, repository_root=root)
        )

        tm.that(resolved.distribution, eq=source.distribution)
        tm.that(resolved.provider, eq=source.provider)
        tm.that(resolved.url, eq=f"{provider.base_url}/{source.distribution}.git")
        tm.that(source.internal_distribution_prefix, eq="flext-")

    def test_flext_line_follows_the_declared_infra_source_not_the_consumer(
        self, tmp_path: Path
    ) -> None:
        """Every internal floor renders from the infra dependency's own source."""
        codegen = config.Infra.codegen
        provider = u.Tests.provider()
        branch = u.Tests.provider_branch()
        root = tmp_path / "other-org-consumer"
        root.mkdir()
        (root / "pyproject.toml").write_text(
            '[project]\nname = "acme-platform"\nversion = "0.1.0"\n'
            f'dependencies = ["flext-core @ git+{provider.base_url}/flext-core.git@'
            f'{branch}"]\n'
            "[dependency-groups]\n"
            f'codegen = ["flext-infra @ git+{provider.base_url}/flext-infra.git@'
            f'{branch}"]\n',
            encoding="utf-8",
        )
        line = tm.ok(
            u.Infra.flext_integration_line(codegen=codegen, repository_root=root)
        )
        tm.that(line.provider, eq=codegen.infra_repository.provider)
        tm.that(line.branch, eq=branch)
        tm.that(line.base_url, eq=provider.base_url)
        tm.that(line.organization, eq=provider.organization)

    def test_flext_line_fails_loud_on_conflicting_infra_sources(
        self, tmp_path: Path
    ) -> None:
        """Family members declared from two lines in one document are a defect."""
        codegen = config.Infra.codegen
        provider = u.Tests.provider()
        branch = u.Tests.provider_branch()
        root = tmp_path / "split-consumer"
        root.mkdir()
        (root / "pyproject.toml").write_text(
            '[project]\nname = "acme-platform"\nversion = "0.1.0"\n'
            f'dependencies = ["flext-infra @ git+{provider.base_url}/flext-infra.git@'
            f'{branch}"]\n'
            "[dependency-groups]\n"
            'codegen = ["flext-infra @ git+https://github.com/other-org/'
            'flext-infra.git@dev"]\n',
            encoding="utf-8",
        )
        result = u.Infra.flext_integration_line(codegen=codegen, repository_root=root)
        tm.that(result.failure, eq=True)
        tm.that(result.error, has="conflicting flext-* line sources")

    def test_infra_repository_identity_fails_loud_when_undeclared(
        self, tmp_path: Path
    ) -> None:
        """A checkout that declares the infra distribution nowhere fails loudly."""
        codegen = config.Infra.codegen
        root = tmp_path / "undeclared-checkout"
        root.mkdir()
        (root / "pyproject.toml").write_text(
            '[project]\nname = "acme-platform"\nversion = "0.1.0"\ndependencies = []\n',
            encoding="utf-8",
        )

        result = u.Infra.configured_repository_ref(
            codegen=codegen, repository_root=root
        )

        tm.that(result.failure, eq=True)
        tm.that(result.error, has="is undeclared by this checkout")

    def test_beads_toolchain_resolves_the_latest_fork_release(self) -> None:
        tm.that(config.Infra.codegen.toolchain.beads.version, eq="latest")

    def test_bootstrap_toolchain_tracks_latest_mise_release(self) -> None:
        template = (
            Path(__file__).parents[3]
            / "src/flext_infra/templates/project/base/tool_bootstrap_recipe.j2"
        ).read_text(encoding="utf-8")
        tm.that(template, lacks="latest_release_url")
        tm.that(template, lacks="curl ")
        tm.that(template, lacks="--windows --version")
        tm.that(template, lacks="mise_install_path=")
        tm.that(template, has='latest_mise="$$mise"')
        tm.that(template, has="receipt_runtime")
        tm.that(
            tuple(type(config.Infra.codegen.toolchain).model_fields),
            lacks="mise_version",
        )

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
        tm.that(
            content,
            has='"$${SETUP_DIRENV:?missing Mise-resolved direnv executable}" allow',
        )
        mise_template = template.with_name(".mise.toml.j2").read_text(encoding="utf-8")
        tm.that(mise_template, has='direnv = "{{ direnv_version }}"')
        tm.that(mise_template, has='go = "{{ go_version }}"')
        tm.that(mise_template, has='make = "{{ make_version }}"')
        tm.that(mise_template, lacks="credential_command")
        tm.that(mise_template, lacks="minimum_release_age")
        # S1 (operator law 2026-09-14): gen has one always-apply recipe; the
        # CHECK_ONLY-selected check/apply pair no longer exists.
        tm.that("_builtin_gen_check:" in content, eq=False)
        tm.that("_builtin_gen_apply:" in content, eq=False)
        tm.that("_builtin_gen_all:" in content, eq=True)
        bootstrap = template.with_name("tool_bootstrap_recipe.j2").read_text(
            encoding="utf-8"
        )
        tm.that(bootstrap, lacks="latest_release_url")
        tm.that(bootstrap, lacks="curl ")
        tm.that(bootstrap, lacks="GH_CONFIG_DIR")
        tm.that(bootstrap, lacks="self-update")
        tm.that("mise launcher version mismatch" in bootstrap, eq=False)
        verb_names = {verb.name for verb in config.Infra.codegen.make.verbs}
        tm.that(verb_names, has="setup")
        tm.that(verb_names, has="gen")

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
            "ManagedArtifacts:\n  Mise:\n    tools:\n      node:\n        version: '26'\n",
            encoding="utf-8",
        )
        # The composer reads the committed catalog: the overlay must be in HEAD.
        u.Tests.initialize_git_repo(tmp_path)

        result = FlextInfraCodegenConform.compose_project_artifact(
            tmp_path, c.Infra.MISE_TOML_FILENAME, '[tools]\npython = "3.13"\n'
        )

        rendered = u.Tests.toml_payload(tm.ok(result).rendered)
        tm.that(rendered["tools"], eq={"python": "3.13", "node": "26"})

    def test_local_manifest_conforms_without_global_repository_rows(
        self, tmp_path: Path
    ) -> None:
        root = self._repository(
            "acme-platform", path=".", role=c.Infra.MakeProfile.WORKSPACE
        )
        member = self._repository(
            "acme-charts", path="acme-charts", role=c.Infra.MakeProfile.STANDALONE
        )
        workspace = m.Infra.WorkspaceSpec(
            name=root.name,
            beads=u.Tests.beads_project(root.name),
            repository=root,
            project=u.Tests.project_spec(root.name),
            subprojects=(member,),
        )
        member_source = tmp_path / "member-source"
        u.Tests.WorktreeFixture.initialize_governed_project(
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
                f"refs/heads/{u.Tests.provider_branch()}",
                member_head,
            ])
        )

        repository_root = tmp_path / "workspace"
        u.Tests.WorktreeFixture.initialize_governed_project(
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
                    u.Tests.provider_branch(),
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
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "update-ref",
                    f"refs/remotes/origin/{u.Tests.provider_branch()}",
                    member_head,
                ],
                cwd=member_checkout,
            )
        )
        gitmodules = u.Tests.WorktreeFixture.write_gitmodules(
            repository_root, (member.name,)
        )
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
                    f"refs/remotes/origin/{u.Tests.provider_branch()}",
                    root_head,
                ],
                cwd=repository_root,
            )
        )
        declared_gitmodules = gitmodules.read_bytes()
        result = FlextInfraCodegenConform(initial_workspace=workspace).plan(
            u.Tests.conform_request(
                repository_root,
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
        tm.that(
            u.Tests.codegen_file_text(root_makefile),
            has=f"WORKSPACE_SUBPROJECTS := {member.name}",
        )
        # .gitmodules is externally owned: conform plans no file for it and
        # leaves the declared topology bytes untouched.
        tm.that(tuple(file.path for file in plan.files), lacks=gitmodules.resolve())
        tm.that(gitmodules.read_bytes(), eq=declared_gitmodules)


__all__: list[str] = ["TestsFlextInfraCodegenCatalogExtensions"]
