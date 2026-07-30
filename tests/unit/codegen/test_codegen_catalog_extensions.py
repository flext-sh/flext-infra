"""Repository-local workspace manifests are the sole consumer authority."""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_infra import c, config, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import u


def _repository(
    name: str,
    *,
    path: str,
    role: c.Infra.RepositoryRole,
    state: c.Infra.RepositoryState = c.Infra.RepositoryState.ACTIVE,
) -> m.Infra.RepositoryRef:
    provider = config.Infra.codegen.providers[0]
    return m.Infra.RepositoryRef(
        name=name,
        distribution=name,
        provider=provider.name,
        url=f"{provider.base_url}/{name}.git",
        path=Path(path),
        role=role,
        state=state,
        checkout=(
            c.Infra.CheckoutKind.ROOT
            if role is c.Infra.RepositoryRole.WORKSPACE_ROOT
            else c.Infra.CheckoutKind.SUBMODULE
        ),
        codegen=c.Infra.CodegenKind.CONFORM,
        package=role is c.Infra.RepositoryRole.WORKSPACE_MEMBER,
        editable=role is c.Infra.RepositoryRole.WORKSPACE_MEMBER,
        read_only=False,
    )


class TestsCodegenCatalogExtensions:
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

        # uv is supplied by the caller environment and is deliberately not pinned;
        # only the mise binary and the Beads CLI installed through mise declare
        # immutable selectors: a semver release for mise, and either a semver
        # release or a full commit for the Beads go-module pin.
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

    def test_beads_gate_compares_the_binary_reported_version(self) -> None:
        """The conform preflight gate uses the binary's self-reported version.

        The pinned Beads build is a go-module commit (schema v61-capable) whose
        ``bd version`` output does NOT echo the pin. The toolchain therefore
        declares ``reported_version`` — what the binary actually prints — and
        the gate consumes it via ``gate_version`` so preflight compares like
        with like. (mro-e9j0.6 / shared mro ledger at Dolt schema v61)
        """
        beads = config.Infra.codegen.toolchain.beads
        tm.that(beads.selector, eq="go:github.com/steveyegge/beads/cmd/bd")
        is_commit = len(beads.version) == 40 and all(
            char in "0123456789abcdef" for char in beads.version
        )
        tm.that(is_commit, eq=True)
        tm.that(beads.reported_version, eq="1.1.0")
        tm.that(beads.gate_version, eq="1.1.0")

    def test_conform_has_no_global_workspace_catalog_validator(self) -> None:
        tm.that(
            hasattr(FlextInfraCodegenConform, "_validate_workspace_catalog"), eq=False
        )

    def test_local_manifest_conforms_without_global_repository_rows(
        self, tmp_path: Path
    ) -> None:
        root = _repository(
            "acme-platform", path=".", role=c.Infra.RepositoryRole.WORKSPACE_ROOT
        ).model_copy(
            update={
                "extra_verbs": (
                    m.Infra.MakeVerbSpec(name="audit", default_what="all"),
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
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=root.name,
            repository=root,
            project=project,
            members=(
                _repository(
                    "acme-charts",
                    path="acme-charts",
                    role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
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
                ["git", "add", c.Infra.PYPROJECT_FILENAME], cwd=member_root
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
        bare_repo = tmp_path.parent / "acme-charts-bare.git"
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "clone",
                    "--bare",
                    member_root.as_posix(),
                    bare_repo.as_posix(),
                ]
            )
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
        provider = config.Infra.codegen.providers[0]
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
            u.Cli.atomic_write_text_file(
                tmp_path / c.Infra.PYPROJECT_FILENAME,
                '[project]\nname = "acme-platform"\nversion = "0.1.0"\n'
                'requires-python = ">=3.13,<3.14"\ndependencies = []\n',
            )
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
                ["git", "add", c.Infra.PYPROJECT_FILENAME, c.Infra.GITMODULES],
                cwd=tmp_path,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Workspace fixture"], cwd=tmp_path
            )
        )
        tm.ok(u.Cli.run_checked(["rm", "-rf", bare_repo.as_posix()]))
        manifest_path = tmp_path / "config" / c.Infra.WORKSPACE_MANIFEST_FILENAME
        manifest_path.parent.mkdir(parents=True)
        tm.ok(
            u.Cli.yaml_dump(
                manifest_path,
                workspace.model_dump(mode="json", exclude_none=True),
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
        tm.that(root_makefile.rendered, has="WORKSPACE_MEMBERS := acme-charts")
        tm.that("acme-content" in root_makefile.rendered, eq=False)
        workflows = tuple(
            file for file in plan.files if ".github/workflows" in file.path.as_posix()
        )
        tm.that(workflows, len=4)
        for workflow in workflows:
            tm.that("acme-content" in workflow.rendered, eq=False)
        gitmodules = next(
            file.rendered for file in plan.files if file.path.name == ".gitmodules"
        )
        tm.that(gitmodules, has='[submodule "acme-charts"]')
        tm.that("acme-content" in gitmodules, eq=False)
        mise = tomllib.loads(
            next(file.rendered for file in plan.files if file.path.name == ".mise.toml")
        )
        tm.that(
            mise["tools"]["go:github.com/steveyegge/beads/cmd/bd"],
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
