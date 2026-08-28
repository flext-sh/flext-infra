"""Repository-local codegen extension contracts."""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_infra import c, config, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import WorktreeFixture, u


def _repository(
    name: str,
    *,
    path: str,
    role: c.Infra.RepositoryRole,
    state: c.Infra.RepositoryState = c.Infra.RepositoryState.ACTIVE,
) -> m.Infra.RepositoryRef:
    reference = u.Tests.repository_ref(name, path=Path(path), role=role)
    return reference.model_copy(
        update={
            "state": state,
            "package": role is c.Infra.RepositoryRole.STANDALONE,
            "editable": role is c.Infra.RepositoryRole.STANDALONE,
        }
    )


class TestsCodegenCatalogExtensions:
    """Prove generic extensions without a repository registry or second manifest."""

    def test_infra_repository_identity_is_owned_by_codegen_config(self) -> None:
        source = config.Infra.codegen.infra_repository
        providers = tuple(
            provider
            for provider in config.Infra.codegen.providers
            if provider.name == source.provider
        )

        tm.that(source.distribution, eq=config.Infra.name)
        tm.that(source.internal_distribution_prefix, eq="flext-")
        tm.that(providers, len=1)

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
        ).model_copy(
            update={
                "extra_verbs": (
                    m.Infra.MakeVerbSpec(
                        name="audit",
                        default_what="all",
                        whats=("all",),
                        apply_what="all",
                    ),
                ),
                "script_dispatch": m.Infra.ScriptDispatchSpec(
                    dispatcher="scripts/dispatch.py", roots=("scripts",)
                ),
            }
        )
        project = m.Infra.ProjectSpec(
            package_name="acme_platform",
            class_stem="AcmePlatform",
            namespace="AcmePlatform",
            constant_name="acme-platform",
            namespace_attribute="acme_platform",
            alias="acme",
            environment_prefix="ACME_PLATFORM_",
            description="Product-neutral platform fixture",
            version="0.1.0",
            license="MIT",
            author_name="Acme Team",
            author_email="engineering@example.com",
            upstream="flext_core",
            homepage="https://example.com/acme-platform",
            documentation="https://example.com/acme-platform/docs",
            workspace_root_rel=".",
            year=2026,
        )
        workspace = m.Infra.WorkspaceSpec(
            name=root.name,
            beads=u.Tests.beads_project(root.name),
            repository=root,
            project=project,
            subprojects=(
                _repository(
                    "acme-charts",
                    path="acme-charts",
                    role=c.Infra.RepositoryRole.STANDALONE,
                ),
            ),
        )
        member_root = tmp_path / "acme-charts"
        member_root.mkdir()
        (member_root / c.Infra.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "acme-charts"\nversion = "0.1.0"\n'
            'requires-python = ">=3.13,<3.14"\ndependencies = []\n',
            encoding="utf-8",
        )
        WorktreeFixture.write_beads_project(
            member_root,
            workspace="acme-charts",
            database="acme-charts",
            issue_prefix="acme-charts",
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "init", "-q", "-b", "development"], cwd=member_root
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.email", "infra@example.com"], cwd=member_root
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.name", "Infra Tests"], cwd=member_root
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "add", c.Infra.PYPROJECT_FILENAME, "config/beads.yaml"],
                cwd=member_root,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Initial fixture"], cwd=member_root
            )
        )
        # Register acme-charts as a real Git submodule so workspace root
        # resolution and analysis exclusion discovery observe the attached
        # topology. A local bare repo is used because Git file transport is
        # disabled by default in current releases.
        provider = u.Tests.provider()
        member_baseline = tm.ok(
            u.Cli.capture(["git", "rev-parse", "HEAD"], cwd=member_root)
        )
        bare_repo = tmp_path.parent / "acme-charts-bare.git"
        tm.ok(
            u.Cli.run_checked([
                "git",
                "clone",
                "--bare",
                member_root.as_posix(),
                bare_repo.as_posix(),
            ])
        )
        tm.ok(
            u.Cli.run_checked([
                "git",
                "--git-dir",
                bare_repo.as_posix(),
                "update-ref",
                f"refs/heads/{provider.branch}",
                member_baseline,
            ])
        )
        tm.ok(u.Cli.run_checked(["rm", "-rf", member_root.as_posix()]))
        tm.ok(u.Cli.run_checked(["git", "init", "-q"], cwd=tmp_path))
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    bare_repo.as_posix(),
                    "acme-charts",
                ],
                cwd=tmp_path,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "config",
                    "remote.origin.url",
                    f"{provider.base_url}/acme-charts.git",
                ],
                cwd=member_root,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "remote.origin.skipDefaultUpdate", "true"],
                cwd=member_root,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "update-ref",
                    f"refs/remotes/origin/{provider.branch}",
                    member_baseline,
                ],
                cwd=member_root,
            )
        )
        tm.ok(u.Cli.run_checked(["rm", "-rf", bare_repo.as_posix()]))
        tm.ok(
            u.Cli.atomic_write_text_file(
                tmp_path / c.Infra.PYPROJECT_FILENAME,
                '[project]\nname = "acme-platform"\nversion = "0.1.0"\n'
                'requires-python = ">=3.13,<3.14"\ndependencies = []\n',
            )
        )
        WorktreeFixture.write_beads_project(
            tmp_path, workspace=root.name, database=root.name, issue_prefix=root.name
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                tmp_path / c.Infra.GITMODULES,
                '[submodule "acme-charts"]\n'
                f"    path = acme-charts\n"
                f"    url = {provider.base_url}/acme-charts.git\n"
                f"    branch = {provider.branch}\n",
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.email", "infra@example.com"], cwd=tmp_path
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.name", "Infra Tests"], cwd=tmp_path
            )
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "add",
                    c.Infra.PYPROJECT_FILENAME,
                    c.Infra.GITMODULES,
                    "config/beads.yaml",
                ],
                cwd=tmp_path,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Workspace fixture"], cwd=tmp_path
            )
        )
        root_baseline = tm.ok(u.Cli.capture(["git", "rev-parse", "HEAD"], cwd=tmp_path))
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "update-ref",
                    f"refs/remotes/origin/{provider.branch}",
                    root_baseline,
                ],
                cwd=tmp_path,
            )
        )
        result = FlextInfraCodegenConform(initial_workspace=workspace).plan(
            m.Infra.CodegenConformRequest(
                root=tmp_path,
                what=c.Infra.CodegenConformSurface.ALL,
                scope=c.Infra.CodegenConformScope.ALL,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )

        plan = tm.ok(result)
        tm.that(
            tuple(item.name for item in plan.repositories),
            eq=(root.name, "acme-charts"),
        )
        external_root = (tmp_path / "acme-content").resolve()
        tm.that(
            any(
                external_root == file.path or external_root in file.path.parents
                for file in plan.files
            ),
            eq=False,
        )
        tm.that(external_root.exists(), eq=False)
        root_makefile = next(
            file
            for file in plan.files
            if file.path == tmp_path.resolve() / c.Infra.MAKEFILE_FILENAME
        )
        tm.that(root_makefile.rendered, has="WORKSPACE_SUBPROJECTS := acme-charts")
        tm.that("acme-content" in root_makefile.rendered, eq=False)
        workflows = tuple(
            file for file in plan.files if ".github/workflows" in file.path.as_posix()
        )
        # How many workflows exist is config-owned: freezing the count makes a
        # legitimate template addition fail here. The contract is that every
        # planned workflow is one the config declares, and that none leaks the
        # content-only repository.
        declared_workflows = frozenset(
            entry.destination
            for entry in config.Infra.codegen.templates.entries
            if ".github/workflows" in entry.destination
        )
        tm.that(workflows, empty=False)
        for workflow in workflows:
            tm.that(
                any(
                    workflow.path.as_posix().endswith(destination)
                    for destination in declared_workflows
                ),
                eq=True,
                msg=f"undeclared workflow planned: {workflow.path}",
            )
        for workflow in workflows:
            tm.that("acme-content" in workflow.rendered, eq=False)
        tm.that(
            any(file.path.name == c.Infra.GITMODULES for file in plan.files), eq=False
        )
        gitmodules = (tmp_path / c.Infra.GITMODULES).read_text(encoding="utf-8")
        tm.that(gitmodules, has='[submodule "acme-charts"]')
        tm.that("acme-content" in gitmodules, eq=False)
        mise = tomllib.loads(
            next(file.rendered for file in plan.files if file.path.name == ".mise.toml")
        )
        tm.that(
            mise["tools"][config.Infra.codegen.toolchain.beads.selector]["version"],
            eq=config.Infra.codegen.toolchain.beads.version,
        )
        pyproject = tomllib.loads(
            next(
                file.rendered
                for file in plan.files
                if file.path.name == c.Infra.PYPROJECT_FILENAME
            )
        )
        tools = pyproject["tool"]
        tm.that("acme-content" in tools["ruff"]["exclude"], eq=False)
        tm.that("acme-content" in tools["pyright"]["exclude"], eq=False)


__all__: tuple[str, ...] = ()
